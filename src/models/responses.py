# Response schemas for PeerAgent API
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentType(str, Enum):
    """Types of agents in the system."""
    PEER = "peer_agent"
    CODE = "code_agent"
    CONTENT = "content_agent"
    BUSINESS = "business_sense_agent"
    PROBLEM = "problem_structuring_agent"


class AgentResponse(BaseModel):
    """Base response from any agent."""
    agent_type: AgentType
    success: bool
    data: Any
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TaskResponse(BaseModel):
    """Response for task submission."""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    message: str = Field(default="Task submitted successfully")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "task-abc123",
                    "status": "pending",
                    "message": "Task submitted successfully"
                }
            ]
        }
    }


class TaskStatusResponse(BaseModel):
    """Response for task status check."""
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    agent_type: Optional[AgentType] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "task-abc123",
                    "status": "completed",
                    "result": {"code": "def read_file(path):\n    with open(path) as f:\n        return f.read()"},
                    "agent_type": "code_agent",
                    "created_at": "2024-01-01T00:00:00Z",
                    "completed_at": "2024-01-01T00:00:05Z"
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    code: str = "UNKNOWN_ERROR"
