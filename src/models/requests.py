# Request schemas for PeerAgent API
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TaskInput(BaseModel):
    """Base task input model."""
    task: str = Field(..., min_length=1, description="The task description")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")


class TaskExecuteRequest(BaseModel):
    """Request body for POST /v1/agent/execute."""
    task: str = Field(..., min_length=1, description="The task to execute")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task": "Write a Python function to read a file",
                    "session_id": "user-123-session-abc",
                    "context": {}
                },
                {
                    "task": "My sales are dropping by 20% yearly, help me understand the root cause",
                    "session_id": None,
                    "context": {"industry": "retail"}
                }
            ]
        }
    }


class BusinessQuestionInput(BaseModel):
    """Input for business agent follow-up questions."""
    session_id: str = Field(..., description="Session ID from initial request")
    answers: Dict[str, str] = Field(..., description="Answers to the agent's questions")
