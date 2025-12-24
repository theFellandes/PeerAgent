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
    priority: Optional[int] = Field(
        None, 
        ge=1, 
        le=3, 
        description="Task priority: 3=high (business), 2=medium (code), 1=low (content). Auto-assigned if not provided."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task": "Write a Python function to read a file",
                    "session_id": "user-123-session-abc",
                    "context": {},
                    "priority": 2
                },
                {
                    "task": "My sales are dropping by 20% yearly, help me understand the root cause",
                    "session_id": None,
                    "context": {"industry": "retail"},
                    "priority": 3
                }
            ]
        }
    }


class BusinessQuestionInput(BaseModel):
    """Input for business agent follow-up questions."""
    session_id: str = Field(..., description="Session ID from initial request")
    answers: Dict[str, str] = Field(..., description="Answers to the agent's questions (can be all in one text)")
    answer_round: int = Field(default=1, description="Current answer round number (increments each response)")
    original_task: Optional[str] = Field(None, description="Original business problem statement")
    latest_answer: Optional[str] = Field(None, description="The most recent answer text for validation")
    previous_questions: Optional[List[str]] = Field(None, description="Previous questions to validate against")


