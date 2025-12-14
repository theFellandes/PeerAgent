# PeerAgent Models
"""
Pydantic schemas for requests, responses, and agent outputs.
"""

from src.models.requests import TaskInput, TaskExecuteRequest, BusinessQuestionInput
from src.models.responses import TaskResponse, TaskStatusResponse, AgentResponse, TaskStatus, AgentType
from src.models.agents import (
    BusinessDiagnosis,
    ProblemCause,
    ProblemTree,
    CodeOutput,
    ContentOutput,
    BusinessAgentQuestions,
    FullBusinessAnalysis,
)

__all__ = [
    # Requests
    "TaskInput",
    "TaskExecuteRequest",
    "BusinessQuestionInput",
    # Responses
    "TaskResponse",
    "TaskStatusResponse",
    "AgentResponse",
    "TaskStatus",
    "AgentType",
    # Agent outputs
    "BusinessDiagnosis",
    "ProblemCause",
    "ProblemTree",
    "CodeOutput",
    "ContentOutput",
    "BusinessAgentQuestions",
    "FullBusinessAnalysis",
]
