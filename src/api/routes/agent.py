# Agent API Routes
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import uuid
import json
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
from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent"])

# In-memory task storage (replace with Redis in production)
task_store: dict = {}


def get_peer_agent() -> PeerAgent:
    """Dependency to get PeerAgent instance."""
    return PeerAgent()


@router.post(
    "/execute",
    response_model=TaskResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Execute Agent Task",
    description="""
Submit a task for agent execution.

The task will be analyzed by the PeerAgent which will:
1. Classify the task type (code, content, or business)
2. Route to the appropriate sub-agent
3. Return results or follow-up questions

**Examples:**
- Code: "Write a Python function to read a file"
- Content: "What is machine learning?"
- Business: "Our sales are dropping by 20%, help me understand why"
    """
)
async def execute_task(
    request: TaskExecuteRequest,
    background_tasks: BackgroundTasks,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> TaskResponse:
    """
    Execute a task via the PeerAgent system.
    
    For synchronous processing, the task is executed immediately.
    For async processing (with queue), a task_id is returned for status polling.
    """
    # Validate input
    if not request.task or not request.task.strip():
        raise HTTPException(
            status_code=400,
            detail={"error": "Task cannot be empty", "code": "EMPTY_TASK"}
        )
    
    # Generate task ID
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = request.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Received task {task_id}: {request.task[:100]}...")
    
    # For synchronous mode: execute immediately
    # (Queue mode would push to Celery instead)
    try:
        # Store initial task state
        task_store[task_id] = {
            "task_id": task_id,
            "status": TaskStatus.PROCESSING,
            "task": request.task,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        # Execute the task
        result = await peer_agent.execute(
            task=request.task,
            session_id=session_id,
            task_id=task_id
        )
        
        # Update task state with result
        task_store[task_id].update({
            "status": TaskStatus.COMPLETED,
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
        
        # Update task state with error
        if task_id in task_store:
            task_store[task_id].update({
                "status": TaskStatus.FAILED,
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })
        
        raise HTTPException(
            status_code=500,
            detail={"error": str(e), "code": "EXECUTION_ERROR"}
        )


@router.get(
    "/status/{task_id}",
    response_model=TaskStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task Not Found"}
    },
    summary="Get Task Status",
    description="Retrieve the status and result of a previously submitted task."
)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the status of a task by ID.
    
    Returns the current status, result (if completed), or error (if failed).
    """
    if task_id not in task_store:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Task {task_id} not found", "code": "TASK_NOT_FOUND"}
        )
    
    task_data = task_store[task_id]
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"],
        result=task_data.get("result"),
        error=task_data.get("error"),
        agent_type=task_data.get("agent_type"),
        created_at=task_data.get("created_at"),
        completed_at=task_data.get("completed_at")
    )


@router.post(
    "/execute/direct/{agent_type}",
    response_model=TaskResponse,
    summary="Execute with Specific Agent",
    description="""
Execute a task directly with a specified agent type, bypassing automatic classification.

**Agent Types:**
- `code`: Code generation tasks
- `content`: Research and content tasks  
- `business`: Business problem diagnosis
    """
)
async def execute_direct(
    agent_type: str,
    request: TaskExecuteRequest,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> TaskResponse:
    """Execute a task with a specific agent type."""
    valid_types = ["code", "content", "business"]
    if agent_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid agent type: {agent_type}. Must be one of: {valid_types}",
                "code": "INVALID_AGENT_TYPE"
            }
        )
    
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    session_id = request.session_id or f"session-{uuid.uuid4().hex[:8]}"
    
    try:
        task_store[task_id] = {
            "task_id": task_id,
            "status": TaskStatus.PROCESSING,
            "task": request.task,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None
        }
        
        result = await peer_agent.execute_with_agent_type(
            task=request.task,
            agent_type=agent_type,
            session_id=session_id,
            task_id=task_id
        )
        
        task_store[task_id].update({
            "status": TaskStatus.COMPLETED,
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
        if task_id in task_store:
            task_store[task_id].update({
                "status": TaskStatus.FAILED,
                "error": str(e)
            })
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.post(
    "/business/continue",
    response_model=TaskResponse,
    summary="Continue Business Analysis",
    description="Continue a business analysis session by providing answers to follow-up questions."
)
async def continue_business_analysis(
    request: BusinessQuestionInput,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> TaskResponse:
    """Continue an ongoing business analysis with answers to questions."""
    task_id = f"task-{uuid.uuid4().hex[:12]}"
    
    try:
        # Get business agent directly
        business_agent = peer_agent.business_agent
        
        result = await business_agent.execute(
            task="Continue analysis with provided answers",
            collected_answers=request.answers,
            session_id=request.session_id,
            task_id=task_id
        )
        
        task_store[task_id] = {
            "task_id": task_id,
            "status": TaskStatus.COMPLETED,
            "result": result,
            "session_id": request.session_id,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "agent_type": "business_sense_agent"
        }
        
        return TaskResponse(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            message="Business analysis continued"
        )
        
    except Exception as e:
        logger.error(f"Business continuation failed: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get(
    "/classify",
    summary="Classify Task",
    description="Classify a task without executing it (useful for debugging routing)."
)
async def classify_task(
    task: str,
    peer_agent: PeerAgent = Depends(get_peer_agent)
) -> dict:
    """Classify a task to see which agent would handle it."""
    if not task.strip():
        raise HTTPException(status_code=400, detail={"error": "Task cannot be empty"})
    
    classification = await peer_agent.classify_task(task)
    return {
        "task": task,
        "classification": classification,
        "agent": f"{classification}_agent"
    }
