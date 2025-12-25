# Agent API Routes - Improved with Redis Task Store
"""
Enhanced API routes with:
- Redis-backed persistent task storage
- Better error handling
- Queue integration
- Comprehensive logging
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, Query
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
import uuid
from datetime import datetime

from src.models.requests import TaskExecuteRequest, BusinessQuestionInput
from src.models.responses import (
    TaskResponse,
    TaskStatusResponse,
    TaskStatus,
    ErrorResponse,
    AgentType
)
from src.agents.peer_agent import PeerAgent
from src.utils.task_store import get_task_store, TaskData, TaskStatus as StoreStatus
from src.utils.logger import get_logger
from src.config import get_settings

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

# Rate limiter (shared with main app)
limiter = Limiter(key_func=get_remote_address)


def get_peer_agent() -> PeerAgent:
    """Dependency to get PeerAgent instance."""
    return PeerAgent()


def map_status(store_status: StoreStatus) -> TaskStatus:
    """Map task store status to response status."""
    return TaskStatus(store_status.value)


# ==============================================================================
# Task Execution Endpoints
# ==============================================================================

@router.post(
    "/execute",
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Empty task"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        503: {"model": ErrorResponse, "description": "Service Unavailable - Redis down"}
    },
    summary="Execute Agent Task",
    description="""
Submit a task for agent execution.

The task will be analyzed by the PeerAgent which will:
1. Classify the task type (code, content, or business)
2. Route to the appropriate sub-agent
3. Return results or follow-up questions

**Rate Limit:** 10 requests per minute

**Examples:**
- Code: "Write a Python function to read a file"
- Content: "What is machine learning?"
- Business: "Our sales are dropping by 20%, help me understand why"
    """
)
@limiter.limit("10/minute")
async def execute_task(
    request: Request,
    body: TaskExecuteRequest,
    background_tasks: BackgroundTasks,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> Dict[str, Any]:
    """
    Execute a task via the PeerAgent system.
    
    For synchronous processing, the task is executed immediately.
    Task state is persisted in Redis for durability.
    """
    # Validate input
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    # Generate identifiers
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = body.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Received task {task_id}: {body.task[:100]}...")
    
    # Get task store
    try:
        task_store = get_task_store()
    except Exception as e:
        logger.error(f"Task store unavailable: {e}")
        raise HTTPException(
            status_code=503,
            detail={"error": "Task storage unavailable", "code": "STORAGE_ERROR"}
        )
    
    try:
        # Create initial task record
        task_data = TaskData(
            task_id=task_id,
            status=StoreStatus.PROCESSING,
            task=body.task,
            session_id=session_id,
            metadata=body.context or {}
        )
        task_store.create(task_data)
        
        # Execute the task
        result = await peer_agent.execute(
            task=body.task,
            session_id=session_id,
            task_id=task_id
        )
        
        # Auto-assign priority based on agent type if not provided
        # Business problems get highest priority (3), code medium (2), content low (1)
        priority_map = {
            "business_sense_agent": 3,
            "code_agent": 2,
            "content_agent": 1,
            "peer_agent": 2  # Default to medium
        }
        agent_type = result.get("agent_type", "peer_agent")
        priority = body.priority or priority_map.get(agent_type, 2)
        
        logger.info(f"Task {task_id} completed | agent={agent_type} | priority={priority}")
        
        # Update task with result
        task_store.update(task_id, {
            "status": StoreStatus.COMPLETED,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
            "agent_type": agent_type,
            "priority": priority
        })
        
        # Return result directly (no polling needed)
        return {
            "task_id": task_id,
            "status": "completed",
            "agent_type": agent_type,
            "priority": priority,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        
        # Update task with error
        try:
            task_store.update(task_id, {
                "status": StoreStatus.FAILED,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
        except Exception:
            pass  # Best effort
        
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "code": "EXECUTION_ERROR"}
        )


@router.post(
    "/execute/stream",
    summary="Execute with Streaming Response",
    description="""
Execute a task with Server-Sent Events (SSE) streaming.

The response is streamed as SSE events, with each chunk containing a portion 
of the LLM response. Use this for long-running tasks where you want to show
progressive output to the user.

**Event Types:**
- `data: {"content": "..."}` - A chunk of the response
- `data: {"done": true}` - Stream completed
- `data: {"error": "..."}` - An error occurred

**Rate Limit:** 5 requests per minute
    """
)
@limiter.limit("5/minute")
async def execute_task_stream(
    request: Request,
    body: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
):
    """Execute a task with streaming SSE response."""
    from src.api.streaming import create_sse_response, stream_llm_response
    
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    task_id = f"task-stream-{uuid.uuid4().hex[:8]}"
    session_id = body.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Starting streamed task {task_id}: {body.task[:50]}...")
    
    async def generate_stream():
        """Generate streaming response."""
        import json
        
        # Classify the task first
        classification = await peer_agent.classify_task(body.task)
        yield f"data: {json.dumps({'event': 'classification', 'agent': classification})}\n\n"
        
        # Get the appropriate agent
        if classification == "code":
            agent = peer_agent.code_agent
        elif classification == "content":
            agent = peer_agent.content_agent
        elif classification == "business":
            agent = peer_agent.business_agent
        else:
            agent = peer_agent
        
        # Stream the LLM response
        messages = agent.create_messages(body.task)
        
        full_response = ""
        async for chunk in agent.llm.astream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield f"data: {json.dumps({'content': chunk.content})}\n\n"
        
        # Send completion with metadata
        priority_map = {"business_sense_agent": 3, "code_agent": 2, "content_agent": 1}
        priority = body.priority or priority_map.get(agent.agent_type, 2)
        
        yield f"data: {json.dumps({'done': True, 'agent_type': agent.agent_type, 'priority': priority, 'task_id': task_id})}\n\n"
    
    from starlette.responses import StreamingResponse
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post(
    "/execute/async",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"}
    },
    summary="Execute Task Asynchronously",
    description="""
Submit a task for asynchronous execution via Celery queue.

Returns immediately with a task_id for status polling.

**Rate Limit:** 10 requests per minute
    """
)
@limiter.limit("10/minute")
async def execute_task_async(
    request: Request,
    body: TaskExecuteRequest,
    background_tasks: BackgroundTasks
) -> TaskResponse:
    """
    Submit a task to the Celery queue for async processing.
    """
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = body.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    # Create task record
    task_store = get_task_store()
    task_data = TaskData(
        task_id=task_id,
        status=StoreStatus.PENDING,
        task=body.task,
        session_id=session_id,
        metadata={"async": True, **(body.context or {})}
    )
    task_store.create(task_data)
    
    # Queue the task
    try:
        from src.worker.tasks import execute_agent_task
        execute_agent_task.delay(
            task=body.task,
            session_id=session_id,
            task_id=task_id,
            context=body.context
        )
        
        logger.info(f"Task {task_id} queued for async processing")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="Task queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Failed to queue task {task_id}: {e}")
        task_store.update(task_id, {
            "status": StoreStatus.FAILED,
            "error": f"Queue error: {e}"
        })
        raise HTTPException(
            status_code=500,
            detail={"error": f"Failed to queue task: {e}", "code": "QUEUE_ERROR"}
        )


# ==============================================================================
# Task Status Endpoints
# ==============================================================================

@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task Not Found"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"}
    },
    summary="Get Task Status",
    description="Retrieve the status and result of a previously submitted task. **Rate Limit:** 30 requests per minute"
)
@limiter.limit("30/minute")
async def get_task_status(request: Request, task_id: str) -> TaskStatusResponse:
    """
    Get the status of a task by ID.
    """
    task_store = get_task_store()
    task_data = task_store.get(task_id)
    
    if task_data is None:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Task {task_id} not found", "code": "TASK_NOT_FOUND"}
        )
    
    return TaskStatusResponse(
        task_id=task_id,
        status=map_status(task_data.status),
        result=task_data.result,
        error=task_data.error,
        agent_type=task_data.agent_type,
        created_at=task_data.created_at,
        completed_at=task_data.completed_at
    )


@router.get(
    "/tasks",
    response_model=List[TaskStatusResponse],
    summary="List Tasks",
    description="List recent tasks with optional filtering."
)
@limiter.limit("20/minute")
async def list_tasks(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    session_id: Optional[str] = Query(default=None)
) -> List[TaskStatusResponse]:
    """
    List tasks with optional filtering.
    """
    task_store = get_task_store()
    
    # Get tasks
    if session_id:
        tasks = task_store.get_session_tasks(session_id, limit=limit)
    else:
        status_filter = StoreStatus(status) if status else None
        tasks = task_store.list_tasks(limit=limit, offset=offset, status=status_filter)
    
    return [
        TaskStatusResponse(
            task_id=t.task_id,
            status=map_status(t.status),
            result=t.result,
            error=t.error,
            agent_type=t.agent_type,
            created_at=t.created_at,
            completed_at=t.completed_at
        )
        for t in tasks
    ]


@router.delete(
    "/tasks/{task_id}",
    summary="Delete Task",
    description="Delete a task record."
)
async def delete_task(task_id: str) -> dict:
    """Delete a task from the store."""
    task_store = get_task_store()
    
    if not task_store.exists(task_id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Task {task_id} not found", "code": "TASK_NOT_FOUND"}
        )
    
    task_store.delete(task_id)
    return {"deleted": task_id}


# ==============================================================================
# Direct Agent Execution
# ==============================================================================

@router.post(
    "/execute/direct/{agent_type}",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid agent type"},
        429: {"model": ErrorResponse, "description": "Rate Limit Exceeded"}
    },
    summary="Execute with Specific Agent",
    description="""
Execute a task directly with a specified agent type, bypassing automatic classification.

**Rate Limit:** 10 requests per minute

**Agent Types:**
- `code`: Code generation tasks
- `content`: Research and content tasks  
- `business`: Business problem diagnosis
- `problem`: Problem structuring (requires prior diagnosis)
    """
)
@limiter.limit("10/minute")
async def execute_direct(
    request: Request,
    agent_type: str,
    body: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> Dict[str, Any]:
    """Execute a task with a specific agent type."""
    valid_types = ["code", "content", "business", "problem", "summary", "translate", "email", "data", "competitor"]
    
    if agent_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid agent type: {agent_type}. Must be one of: {valid_types}",
                "code": "INVALID_AGENT_TYPE"
            }
        )
    
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = body.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    task_store = get_task_store()
    
    try:
        # Create task record
        task_data = TaskData(
            task_id=task_id,
            status=StoreStatus.PROCESSING,
            task=body.task,
            session_id=session_id,
            metadata={"direct": True, "agent_type": agent_type}
        )
        task_store.create(task_data)
        
        # Execute with specific agent
        result = await peer_agent.execute_with_agent_type(
            task=body.task,
            agent_type=agent_type,
            session_id=session_id,
            task_id=task_id
        )
        
        # Update task
        task_store.update(task_id, {
            "status": StoreStatus.COMPLETED,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
            "agent_type": result.get("agent_type")
        })
        
        # Return result directly (no polling needed)
        return {
            "task_id": task_id,
            "status": "completed",
            "agent_type": result.get("agent_type"),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Direct execution failed: {e}")
        task_store.update(task_id, {
            "status": StoreStatus.FAILED,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ==============================================================================
# Business Analysis Endpoints
# ==============================================================================

@router.post(
    "/business/continue",
    summary="Continue Business Analysis",
    description="Continue a business analysis session by providing answers to follow-up questions. Returns result directly."
)
async def continue_business_analysis(
    body: BusinessQuestionInput,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> Dict[str, Any]:
    """Continue an ongoing business analysis with answers to questions.
    
    Returns the result directly in the response body, no need to poll for status.
    """
    if not body.answers:
        raise HTTPException(
            status_code=400,
            detail={"error": "Answers cannot be empty", "code": "EMPTY_ANSWERS"}
        )
    
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    task_store = get_task_store()
    
    try:
        # Get business agent directly
        business_agent = peer_agent.business_agent
        
        # Get previous task from session for context
        session_tasks = task_store.get_session_tasks(body.session_id, limit=5)
        previous_task = ""
        for t in session_tasks:
            if t.task and t.task != "Business analysis continuation":
                previous_task = t.task
                break
        
        # Use original_task from request if provided, otherwise use from session
        task_to_use = body.original_task or previous_task or "Continue analysis with provided answers"
        
        result = await business_agent.execute(
            task=task_to_use,
            collected_answers=body.answers,
            answer_rounds=body.answer_round,
            session_id=body.session_id,
            task_id=task_id,
            latest_answer=body.latest_answer,
            previous_questions=body.previous_questions
        )
        
        # Properly serialize the result
        result_data = result.get("data")
        serialized_result = {
            "agent_type": "business_sense_agent",
            "type": result.get("type"),
            "data": result_data.model_dump() if hasattr(result_data, 'model_dump') else result_data
        }
        
        # Store result for session history
        task_data = TaskData(
            task_id=task_id,
            status=StoreStatus.COMPLETED,
            task="Business analysis continuation",
            session_id=body.session_id,
            result=serialized_result,
            agent_type="business_sense_agent",
            completed_at=datetime.utcnow().isoformat()
        )
        task_store.create(task_data)
        
        # Return result directly in response (no need to poll)
        return {
            "task_id": task_id,
            "status": "completed",
            "agent_type": "business_sense_agent",
            "result": serialized_result
        }
        
    except Exception as e:
        logger.error(f"Business continuation failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.post(
    "/business/demo",
    summary="Business Demo",
    description="Run a complete demo of the business Socratic questioning flow. The LLM generates both questions AND answers automatically."
)
@limiter.limit("5/minute")
async def business_demo(
    request: Request,
    body: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> Dict[str, Any]:
    """
    Run a complete business diagnosis demo.
    
    The LLM generates questions for each phase and then generates
    realistic answers to those questions, simulating a full conversation.
    """
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    try:
        business_agent = peer_agent.business_agent
        result = await business_agent.execute_demo(task=body.task)
        
        return {
            "task_id": f"demo-{uuid.uuid4().hex[:8]}",
            "status": "completed",
            "agent_type": "business_sense_agent",
            "demo_mode": True,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Demo failed: {str(e)}", "code": "DEMO_ERROR"}
        )


@router.post(
    "/business/problem-tree",
    summary="Problem Tree Demo",
    description="""
Generate a Problem Tree (Issue Tree) directly from a business problem description.

This endpoint demonstrates **Output 2** from the PDF requirements:
- Problem Type Classification (Growth, Cost, Operational, Technology, Regulation, Organizational)
- Structured Problem Tree with 3-5 root causes
- Each root cause has 2-3 sub-causes
- Follows MECE (Mutually Exclusive, Collectively Exhaustive) principles

**Rate Limit:** 5 requests per minute
    """
)
@limiter.limit("5/minute")
async def problem_tree_demo(
    request: Request,
    body: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> Dict[str, Any]:
    """
    Generate a Problem Tree directly from a problem description.
    
    This is a quick way to demonstrate the Problem Structuring Agent
    without going through the full Socratic questioning flow.
    """
    if not body.task or not body.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Problem description cannot be empty", "code": "EMPTY_TASK"}
        )
    
    try:
        # Use ProblemStructuringAgent's structure_from_text method
        problem_agent = peer_agent.problem_agent
        problem_tree = await problem_agent.structure_from_text(
            problem_description=body.task,
            session_id=body.session_id
        )
        
        return {
            "task_id": f"tree-{uuid.uuid4().hex[:8]}",
            "status": "completed",
            "agent_type": "problem_structuring_agent",
            "result": {
                "type": "problem_tree",
                "problem_description": body.task,
                "problem_tree": problem_tree.model_dump()
            }
        }
        
    except Exception as e:
        logger.error(f"Problem tree generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": f"Problem tree generation failed: {str(e)}", "code": "TREE_ERROR"}
        )


# ==============================================================================
# Utility Endpoints
# ==============================================================================

@router.get(
    "/classify",
    summary="Classify Task",
    description="Classify a task without executing it (useful for debugging routing)."
)
async def classify_task(
    task: str = Query(..., min_length=1),
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> dict:
    """Classify a task to see which agent would handle it."""
    classification = await peer_agent.classify_task(task)
    
    # Get keyword matches for debugging
    keyword_result = peer_agent._keyword_classify(task)
    
    return {
        "task": task,
        "classification": classification,
        "agent": f"{classification}_agent",
        "routing_method": "keyword" if keyword_result else "llm",
        "keyword_match": keyword_result
    }


@router.get(
    "/stats",
    summary="Get Task Statistics",
    description="Get statistics about task processing."
)
async def get_stats() -> dict:
    """Get task store statistics."""
    task_store = get_task_store()
    return task_store.get_stats()
