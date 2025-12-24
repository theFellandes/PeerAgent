# Celery Tasks for PeerAgent
import asyncio
from typing import Any, Dict, Optional
from celery import shared_task
from datetime import datetime

from src.worker.celery_app import celery_app
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="execute_agent_task")
def execute_agent_task(
    self,
    task: str,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute a task via PeerAgent asynchronously.
    
    This task is queued by FastAPI and processed by Celery workers.
    
    Args:
        task: The task description
        session_id: Session ID for tracking
        task_id: Task ID for tracking
        context: Additional context
        
    Returns:
        Dict with agent result or error
    """
    logger.info(f"Celery task started: {task_id} - {task[:50]}...")
    
    async def _execute():
        from src.agents.peer_agent import PeerAgent
        
        peer_agent = PeerAgent(session_id=session_id)
        result = await peer_agent.execute(
            task=task,
            session_id=session_id,
            task_id=task_id
        )
        return result
    
    try:
        result = run_async(_execute())
        logger.info(f"Celery task completed: {task_id}")
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Celery task failed: {task_id} - {e}")
        # Optionally retry
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }

# TODO: Maybe add task prioritization, e.g., high, medium, low to Celery queues
# Justification: "In a real consulting scenario, a client asking 'Our sales dropped 20% - help diagnose'
# is more urgent than 'What is machine learning?' Priority queuing ensures business-critical
# workflows aren't blocked by informational queries."
@celery_app.task(bind=True, name="execute_business_task")
def execute_business_task(
    self,
    task: str,
    collected_answers: Optional[Dict[str, str]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute a business analysis task specifically.
    
    Args:
        task: The business problem description
        collected_answers: Previous Q&A pairs
        session_id: Session ID for tracking
        task_id: Task ID for tracking
        
    Returns:
        Dict with diagnosis or follow-up questions
    """
    logger.info(f"Business task started: {task_id}")
    
    async def _execute():
        from src.agents.business_agent import BusinessSenseAgent
        
        agent = BusinessSenseAgent(session_id=session_id)
        result = await agent.execute(
            task=task,
            collected_answers=collected_answers,
            session_id=session_id,
            task_id=task_id
        )
        return result
    
    try:
        result = run_async(_execute())
        
        # Serialize the result
        data = result.get("data")
        if hasattr(data, "model_dump"):
            result["data"] = data.model_dump()
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result,
            "completed_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Business task failed: {task_id} - {e}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(e)
        }


@celery_app.task(name="health_check")
def health_check() -> Dict[str, str]:
    """Simple health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
