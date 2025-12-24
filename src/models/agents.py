# Agent output schemas for PeerAgent
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class BusinessDiagnosis(BaseModel):
    """Output from BusinessSenseAgent - Initial diagnosis."""
    customer_stated_problem: str = Field(
        ...,
        description="The problem as stated by the customer"
    )
    identified_business_problem: str = Field(
        ...,
        description="The actual business problem identified through analysis"
    )
    hidden_root_risk: str = Field(
        ...,
        description="The hidden underlying risk that may not be immediately apparent"
    )
    urgency_level: Literal["Low", "Medium", "Critical"] = Field(
        ...,
        description="Business urgency level"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_stated_problem": "Our sales are dropping by 20% yearly",
                    "identified_business_problem": "Market share erosion due to competitive pressure and outdated product offering",
                    "hidden_root_risk": "Loss of customer trust and brand perception degradation",
                    "urgency_level": "Critical"
                }
            ]
        }
    }


class ProblemCause(BaseModel):
    """A root cause with its sub-causes."""
    cause: str = Field(..., description="Main cause description")
    sub_causes: List[str] = Field(
        default_factory=list,
        description="List of sub-causes under this main cause"
    )


class ProblemTree(BaseModel):
    """Output from ProblemStructuringAgent - Structured problem analysis."""
    problem_type: Literal[
        "Growth",
        "Cost",
        "Operational",
        "Technology",
        "Regulation",
        "Organizational"
    ] = Field(..., description="Classification of the problem type")
    main_problem: str = Field(..., description="The main problem statement")
    root_causes: List[ProblemCause] = Field(
        default_factory=list,
        description="Structured list of root causes with sub-causes"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "problem_type": "Growth",
                    "main_problem": "Declining Sales",
                    "root_causes": [
                        {
                            "cause": "Marketing Inefficiency",
                            "sub_causes": [
                                "Wrong targeting",
                                "Weak ad optimization",
                                "Low conversion rate"
                            ]
                        },
                        {
                            "cause": "Competitive Pressure",
                            "sub_causes": [
                                "Competitors have lower prices",
                                "Competitor products more differentiated"
                            ]
                        }
                    ]
                }
            ]
        }
    }


class CodeOutput(BaseModel):
    """Output from CodeAgent."""
    code: str = Field(..., description="The generated code")
    language: str = Field(..., description="Programming language")
    explanation: str = Field(..., description="Explanation of the code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "def read_file(path: str) -> str:\n    \"\"\"Read and return file contents.\"\"\"\n    with open(path, 'r', encoding='utf-8') as f:\n        return f.read()",
                    "language": "python",
                    "explanation": "This function opens a file at the given path, reads its contents using UTF-8 encoding, and returns the text as a string."
                }
            ]
        }
    }


class ContentOutput(BaseModel):
    """Output from ContentAgent."""
    content: str = Field(..., description="The generated content")
    sources: List[str] = Field(
        default_factory=list,
        description="List of source URLs used"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": "Machine learning is a subset of artificial intelligence...",
                    "sources": [
                        "https://en.wikipedia.org/wiki/Machine_learning",
                        "https://www.ibm.com/topics/machine-learning"
                    ]
                }
            ]
        }
    }


class BusinessAgentQuestions(BaseModel):
    """Questions from BusinessSenseAgent during Socratic dialogue."""
    session_id: str = Field(..., description="Session ID for tracking the conversation")
    questions: List[str] = Field(..., description="List of clarifying questions")
    category: str = Field(..., description="Category of questions being asked")
    phase: Optional[str] = Field(default=None, description="Current phase: identify, clarify, or diagnose")
    phase_emoji: Optional[str] = Field(default=None, description="Emoji indicator for the phase")
    round_number: Optional[int] = Field(default=None, description="Current questioning round (1, 2, 3...)")
    feedback: Optional[str] = Field(default=None, description="Feedback message if answer validation failed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "sess-abc123",
                    "questions": [
                        "When did this problem first start?",
                        "What percentage drop have you seen?",
                        "Is this problem in your company's TOP 3 priorities?"
                    ],
                    "category": "problem_identification",
                    "phase": "identify",
                    "phase_emoji": "🔍",
                    "round_number": 1,
                    "feedback": None
                }
            ]
        }
    }


class FullBusinessAnalysis(BaseModel):
    """Complete business analysis output combining diagnosis and problem tree."""
    diagnosis: BusinessDiagnosis
    problem_tree: ProblemTree
    recommendations: Optional[List[str]] = Field(
        default=None,
        description="Optional list of recommendations"
    )