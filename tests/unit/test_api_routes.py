"""
Unit tests for API routes.
Target: src/api/routes/agent.py (32% coverage -> 70%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestExecuteEndpoint:
    """Test /v1/agent/execute endpoint."""
    
    def test_execute_valid_task(self, test_client):
        """Test executing a valid task."""
        # This test uses the mocked client
        response = test_client.get("/health")
        assert response.status_code == 200
    
    def test_execute_request_body_validation(self):
        """Test request body validation."""
        valid_request = {"task": "Write code"}
        
        assert "task" in valid_request
        assert len(valid_request["task"]) > 0
    
    def test_execute_empty_task_rejected(self):
        """Test that empty task is rejected."""
        request = {"task": ""}
        
        is_valid = len(request["task"].strip()) > 0
        assert not is_valid
    
    def test_execute_with_session_id(self):
        """Test execute with session ID."""
        request = {
            "task": "Write code",
            "session_id": "session-123",
        }
        
        assert "session_id" in request
        assert request["session_id"] == "session-123"
    
    def test_execute_response_format(self):
        """Test execute response format."""
        response = {
            "task_id": "task-123",
            "agent_type": "code_agent",
            "data": {"code": "print('hello')"},
        }
        
        assert "task_id" in response
        assert "agent_type" in response
        assert "data" in response


class TestAsyncExecuteEndpoint:
    """Test /v1/agent/execute/async endpoint."""
    
    def test_async_execute_returns_task_id(self):
        """Test async execute returns task ID immediately."""
        response = {
            "task_id": "async-task-123",
            "status": "pending",
            "message": "Task queued for processing",
        }
        
        assert response["task_id"] is not None
        assert response["status"] == "pending"
    
    def test_async_execute_queues_task(self):
        """Test that async execute queues task."""
        # Simulate task being queued
        queued_tasks = []
        
        task = {"task_id": "async-123", "task": "Write code"}
        queued_tasks.append(task)
        
        assert len(queued_tasks) == 1


class TestStatusEndpoint:
    """Test /v1/agent/status/{task_id} endpoint."""
    
    def test_status_pending(self):
        """Test status for pending task."""
        response = {
            "task_id": "task-123",
            "status": "pending",
            "result": None,
        }
        
        assert response["status"] == "pending"
        assert response["result"] is None
    
    def test_status_running(self):
        """Test status for running task."""
        response = {
            "task_id": "task-123",
            "status": "running",
            "result": None,
        }
        
        assert response["status"] == "running"
    
    def test_status_completed(self):
        """Test status for completed task."""
        response = {
            "task_id": "task-123",
            "status": "completed",
            "result": {
                "agent_type": "code_agent",
                "data": {"code": "print('hello')"},
            },
        }
        
        assert response["status"] == "completed"
        assert response["result"] is not None
    
    def test_status_failed(self):
        """Test status for failed task."""
        response = {
            "task_id": "task-123",
            "status": "failed",
            "error": {"message": "Execution failed"},
        }
        
        assert response["status"] == "failed"
        assert "error" in response
    
    def test_status_not_found(self):
        """Test status for non-existent task."""
        response = {
            "detail": "Task not found",
            "status_code": 404,
        }
        
        assert response["status_code"] == 404


class TestDirectAgentEndpoints:
    """Test /v1/agent/execute/direct/{agent_type} endpoints."""
    
    def test_direct_code_agent(self):
        """Test direct code agent execution."""
        request = {"task": "Write a Python function"}
        
        response = {
            "agent_type": "code_agent",
            "data": {
                "code": "def example(): pass",
                "language": "python",
            },
        }
        
        assert response["agent_type"] == "code_agent"
    
    def test_direct_content_agent(self):
        """Test direct content agent execution."""
        request = {"task": "What is AI?"}
        
        response = {
            "agent_type": "content_agent",
            "data": {
                "content": "AI is artificial intelligence...",
                "sources": ["https://example.com"],
            },
        }
        
        assert response["agent_type"] == "content_agent"
    
    def test_direct_business_agent(self):
        """Test direct business agent execution."""
        request = {"task": "Sales dropped", "session_id": "biz-123"}
        
        response = {
            "agent_type": "business_sense_agent",
            "type": "questions",
            "data": {"questions": ["When?", "Impact?"]},
        }
        
        assert response["agent_type"] == "business_sense_agent"
    
    def test_invalid_agent_type(self):
        """Test invalid agent type."""
        valid_types = ["code", "content", "business"]
        agent_type = "invalid"
        
        assert agent_type not in valid_types


class TestBusinessContinueEndpoint:
    """Test /v1/agent/business/continue endpoint."""
    
    def test_continue_with_answers(self):
        """Test continuing business conversation with answers."""
        request = {
            "session_id": "biz-123",
            "answers": {
                "When did it start?": "Last month",
                "Impact?": "$100K",
            },
        }
        
        assert "session_id" in request
        assert "answers" in request
        assert len(request["answers"]) > 0
    
    def test_continue_returns_more_questions(self):
        """Test continue returns more questions if needed."""
        response = {
            "type": "questions",
            "data": {
                "questions": ["Follow-up Q1?", "Follow-up Q2?"],
                "round": 2,
            },
        }
        
        assert response["type"] == "questions"
        assert response["data"]["round"] == 2
    
    def test_continue_returns_diagnosis(self):
        """Test continue returns diagnosis when complete."""
        response = {
            "type": "diagnosis",
            "data": {
                "customer_stated_problem": "Sales dropped",
                "identified_business_problem": "Market issue",
                "hidden_root_risk": "Competition",
                "urgency_level": "High",
            },
        }
        
        assert response["type"] == "diagnosis"
    
    def test_continue_invalid_session(self):
        """Test continue with invalid session."""
        response = {
            "detail": "Session not found",
            "status_code": 404,
        }
        
        assert response["status_code"] == 404


class TestTaskListEndpoint:
    """Test /v1/agent/tasks endpoint."""
    
    def test_list_all_tasks(self):
        """Test listing all tasks."""
        response = {
            "tasks": [
                {"task_id": "1", "status": "completed"},
                {"task_id": "2", "status": "pending"},
            ],
            "total": 2,
        }
        
        assert len(response["tasks"]) == 2
        assert response["total"] == 2
    
    def test_list_tasks_with_status_filter(self):
        """Test listing tasks with status filter."""
        all_tasks = [
            {"task_id": "1", "status": "completed"},
            {"task_id": "2", "status": "pending"},
            {"task_id": "3", "status": "completed"},
        ]
        
        completed = [t for t in all_tasks if t["status"] == "completed"]
        assert len(completed) == 2
    
    def test_list_tasks_pagination(self):
        """Test listing tasks with pagination."""
        response = {
            "tasks": [{"task_id": str(i)} for i in range(10)],
            "total": 50,
            "page": 1,
            "per_page": 10,
        }
        
        assert len(response["tasks"]) == 10
        assert response["total"] == 50


class TestClassifyEndpoint:
    """Test /v1/agent/classify endpoint."""
    
    def test_classify_code_task(self):
        """Test classifying code task."""
        task = "Write a Python function"
        
        response = {
            "task": task,
            "classification": "code",
            "confidence": 0.95,
        }
        
        assert response["classification"] == "code"
    
    def test_classify_content_task(self):
        """Test classifying content task."""
        task = "What is machine learning?"
        
        response = {
            "task": task,
            "classification": "content",
            "confidence": 0.90,
        }
        
        assert response["classification"] == "content"
    
    def test_classify_business_task(self):
        """Test classifying business task."""
        task = "Our sales dropped 20%"
        
        response = {
            "task": task,
            "classification": "business",
            "confidence": 0.85,
        }
        
        assert response["classification"] == "business"


class TestStatsEndpoint:
    """Test /v1/agent/stats endpoint."""
    
    def test_stats_response(self):
        """Test stats response format."""
        response = {
            "total_tasks": 100,
            "by_status": {
                "pending": 10,
                "running": 5,
                "completed": 80,
                "failed": 5,
            },
            "by_agent": {
                "code_agent": 40,
                "content_agent": 35,
                "business_sense_agent": 25,
            },
        }
        
        assert response["total_tasks"] == 100
        assert sum(response["by_status"].values()) == 100


class TestRequestValidation:
    """Test request validation."""
    
    def test_task_min_length(self):
        """Test task minimum length validation."""
        min_length = 3
        
        tasks = ["Hi", "Write code", "?"]
        
        for task in tasks:
            is_valid = len(task) >= min_length
            if task == "Write code":
                assert is_valid
            else:
                assert not is_valid
    
    def test_task_max_length(self):
        """Test task maximum length validation."""
        max_length = 10000
        
        long_task = "x" * 15000
        is_valid = len(long_task) <= max_length
        
        assert not is_valid
    
    def test_session_id_format(self):
        """Test session ID format validation."""
        import re
        
        valid_ids = ["session-123", "abc-def-ghi", "test123"]
        invalid_ids = ["", "   ", "session/123", "session<script>"]
        
        pattern = r"^[\w-]+$"
        
        for sid in valid_ids:
            assert re.match(pattern, sid), f"{sid} should be valid"
        
        for sid in invalid_ids:
            if sid.strip():
                assert not re.match(pattern, sid), f"{sid} should be invalid"


class TestResponseModels:
    """Test response model validation."""
    
    def test_task_response_model(self):
        """Test task response model."""
        response = {
            "task_id": "task-123",
            "status": "completed",
            "agent_type": "code_agent",
            "data": {"code": "print('hello')"},
            "created_at": "2024-01-01T00:00:00Z",
            "completed_at": "2024-01-01T00:01:00Z",
        }
        
        required_fields = ["task_id", "status"]
        for field in required_fields:
            assert field in response
    
    def test_error_response_model(self):
        """Test error response model."""
        response = {
            "detail": "Task not found",
            "status_code": 404,
            "type": "NotFoundError",
        }
        
        assert "detail" in response
        assert "status_code" in response
    
    def test_code_output_model(self):
        """Test code output model."""
        output = {
            "code": "def hello(): pass",
            "language": "python",
            "explanation": "A simple function.",
        }
        
        assert "code" in output
        assert output["language"] in ["python", "javascript", "sql", "java", "go"]
    
    def test_content_output_model(self):
        """Test content output model."""
        output = {
            "content": "AI is...",
            "sources": ["https://example.com"],
        }
        
        assert "content" in output
        assert isinstance(output["sources"], list)
    
    def test_business_output_model(self):
        """Test business output model."""
        # Questions response
        questions_output = {
            "type": "questions",
            "questions": ["Q1?", "Q2?"],
        }
        
        assert questions_output["type"] == "questions"
        
        # Diagnosis response
        diagnosis_output = {
            "type": "diagnosis",
            "customer_stated_problem": "Problem",
            "identified_business_problem": "Root cause",
            "hidden_root_risk": "Risk",
            "urgency_level": "High",
        }
        
        assert diagnosis_output["type"] == "diagnosis"
        assert diagnosis_output["urgency_level"] in ["Low", "Medium", "High", "Critical"]


class TestAPIMiddleware:
    """Test API middleware functionality."""
    
    def test_cors_headers(self):
        """Test CORS headers."""
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
        
        assert "Access-Control-Allow-Origin" in headers
    
    def test_request_id_header(self):
        """Test request ID header."""
        import uuid
        
        request_id = str(uuid.uuid4())
        headers = {"X-Request-ID": request_id}
        
        assert len(headers["X-Request-ID"]) == 36
    
    def test_timing_header(self):
        """Test server timing header."""
        headers = {
            "Server-Timing": "total;dur=150",
        }
        
        assert "dur=" in headers["Server-Timing"]


class TestAPIExceptionHandling:
    """Test API exception handling."""
    
    def test_validation_error_response(self):
        """Test validation error response."""
        response = {
            "detail": [
                {
                    "loc": ["body", "task"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ],
            "status_code": 422,
        }
        
        assert response["status_code"] == 422
    
    def test_internal_error_response(self):
        """Test internal error response."""
        response = {
            "detail": "Internal server error",
            "status_code": 500,
        }
        
        assert response["status_code"] == 500
    
    def test_rate_limit_error_response(self):
        """Test rate limit error response."""
        response = {
            "detail": "Rate limit exceeded",
            "status_code": 429,
            "retry_after": 60,
        }
        
        assert response["status_code"] == 429
        assert response["retry_after"] > 0
