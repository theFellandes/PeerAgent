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
    response_model=TaskResponse,
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
) -> TaskResponse:
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
        
        # Update task with result
        task_store.update(task_id, {
            "status": StoreStatus.COMPLETED,
            "result": result,
            "completed_at": datetime.utcnow().isoformat(),
            "agent_type": result.get("agent_type")
        })
        
        logger.info(f"Task {task_id} completed successfully")
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            message="Task executed successfully"
        )
        
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
    response_model=TaskResponse,
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
) -> TaskResponse:
    """Execute a task with a specific agent type."""
    valid_types = ["code", "content", "business", "problem"]
    
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
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            message=f"Task executed with {agent_type} agent"
        )
        
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
