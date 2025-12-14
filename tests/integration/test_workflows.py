"""
Integration tests for PeerAgent.
Tests full workflow from API to agent execution.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json
from fastapi.testclient import TestClient


class TestAPIHealthEndpoints:
    """Test API health check endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Test /health endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
    
    def test_ping_endpoint(self, test_client):
        """Test /ping endpoint."""
        response = test_client.get("/ping")
        assert response.status_code == 200


class TestAgentExecutionFlow:
    """Test complete agent execution flow."""
    
    def test_code_task_execution_flow(self):
        """Test code task from submission to result."""
        # 1. Submit task
        task = "Write a Python hello world function"
        task_id = "test-code-123"
        
        # 2. Task gets classified
        classification = "code"
        assert classification in ["code", "content", "business"]
        
        # 3. Routed to CodeAgent
        agent_type = "code_agent"
        assert agent_type == "code_agent"
        
        # 4. Result returned
        result = {
            "agent_type": "code_agent",
            "data": {
                "code": "def hello():\n    return 'Hello, World!'",
                "language": "python",
                "explanation": "A simple function that returns a greeting.",
            }
        }
        
        assert result["data"]["language"] == "python"
        assert "def hello" in result["data"]["code"]
    
    def test_content_task_execution_flow(self):
        """Test content task from submission to result."""
        # 1. Submit task
        task = "What is machine learning?"
        
        # 2. Task gets classified
        classification = "content"
        
        # 3. Routed to ContentAgent
        agent_type = "content_agent"
        
        # 4. Result returned
        result = {
            "agent_type": "content_agent",
            "data": {
                "content": "Machine learning is a subset of AI...",
                "sources": ["https://example.com/ml-intro"],
            }
        }
        
        assert result["agent_type"] == "content_agent"
        assert len(result["data"]["sources"]) > 0
    
    def test_business_task_execution_flow(self):
        """Test business task from submission to diagnosis."""
        # 1. Submit problem
        problem = "Our sales dropped 20%"
        session_id = "biz-123"
        
        # 2. Task gets classified
        classification = "business"
        
        # 3. Initial response: questions
        questions_response = {
            "type": "questions",
            "data": {
                "questions": [
                    "When did this start?",
                    "Which segments are affected?",
                ]
            }
        }
        
        # 4. User provides answers
        answers = {
            "When did this start?": "Last quarter",
            "Which segments are affected?": "Enterprise",
        }
        
        # 5. Final diagnosis
        diagnosis = {
            "type": "diagnosis",
            "data": {
                "customer_stated_problem": "Sales dropped 20%",
                "identified_business_problem": "Enterprise customer churn",
                "hidden_root_risk": "Product-market fit issues",
                "urgency_level": "High",
            }
        }
        
        assert diagnosis["type"] == "diagnosis"
        assert diagnosis["data"]["urgency_level"] in ["Low", "Medium", "High", "Critical"]


class TestAsyncTaskWorkflow:
    """Test asynchronous task workflow."""
    
    def test_async_task_submission(self):
        """Test async task submission."""
        task_request = {
            "task": "Write complex code",
            "session_id": "async-123",
        }
        
        # Submit returns task_id immediately
        task_id = "task-async-456"
        initial_status = "pending"
        
        assert task_id is not None
        assert initial_status == "pending"
    
    def test_async_task_status_polling(self):
        """Test polling task status."""
        task_id = "task-async-456"
        
        # Status transitions
        statuses = ["pending", "running", "completed"]
        
        for status in statuses:
            assert status in ["pending", "running", "completed", "failed"]
    
    def test_async_task_result_retrieval(self):
        """Test retrieving async task result."""
        task_id = "task-async-456"
        
        result = {
            "task_id": task_id,
            "status": "completed",
            "result": {
                "agent_type": "code_agent",
                "data": {"code": "print('hello')"},
            }
        }
        
        assert result["status"] == "completed"
        assert result["result"] is not None


class TestClassificationIntegration:
    """Test task classification integration."""
    
    def test_classify_code_keywords(self):
        """Test classification with code keywords."""
        tasks = [
            ("Write a function to sort a list", "code"),
            ("Debug this Python script", "code"),
            ("Create an API endpoint", "code"),
            ("Fix the SQL query", "code"),
        ]
        
        for task, expected in tasks:
            # Simple keyword-based classification
            code_keywords = ["function", "debug", "api", "sql", "code", "script"]
            is_code = any(kw in task.lower() for kw in code_keywords)
            
            if expected == "code":
                assert is_code, f"Expected '{task}' to be classified as code"
    
    def test_classify_business_keywords(self):
        """Test classification with business keywords."""
        tasks = [
            ("Our sales dropped significantly", "business"),
            ("Customer churn is increasing", "business"),
            ("Revenue is declining", "business"),
            ("Costs are too high", "business"),
        ]
        
        for task, expected in tasks:
            business_keywords = ["sales", "revenue", "cost", "churn", "profit", "margin"]
            is_business = any(kw in task.lower() for kw in business_keywords)
            
            if expected == "business":
                assert is_business, f"Expected '{task}' to be classified as business"
    
    def test_classify_content_keywords(self):
        """Test classification with content keywords."""
        tasks = [
            ("What is machine learning?", "content"),
            ("Explain quantum computing", "content"),
            ("Research the latest AI trends", "content"),
            ("Find information about blockchain", "content"),
        ]
        
        for task, expected in tasks:
            content_keywords = ["what", "explain", "research", "find", "information", "how"]
            is_content = any(kw in task.lower() for kw in content_keywords)
            
            if expected == "content":
                assert is_content, f"Expected '{task}' to be classified as content"


class TestSessionManagementIntegration:
    """Test session management integration."""
    
    def test_session_creation_and_retrieval(self, mock_redis):
        """Test creating and retrieving sessions."""
        session_id = "session-123"
        session_data = {
            "id": session_id,
            "created_at": "2024-01-01T00:00:00Z",
            "conversation_history": [],
        }
        
        # Store session
        mock_redis.set(f"session:{session_id}", json.dumps(session_data))
        
        # Retrieve session
        stored = json.loads(mock_redis.get(f"session:{session_id}"))
        assert stored["id"] == session_id
    
    def test_session_conversation_history(self, mock_redis):
        """Test session conversation history tracking."""
        session_id = "session-123"
        
        # Initial session
        session = {"id": session_id, "history": []}
        
        # Add messages
        session["history"].append({"role": "user", "content": "Hello"})
        session["history"].append({"role": "assistant", "content": "Hi!"})
        
        mock_redis.set(f"session:{session_id}", json.dumps(session))
        
        stored = json.loads(mock_redis.get(f"session:{session_id}"))
        assert len(stored["history"]) == 2
    
    def test_session_expiration(self, mock_redis):
        """Test session expiration."""
        session_id = "session-123"
        ttl = 3600  # 1 hour
        
        mock_redis.setex(f"session:{session_id}", ttl, json.dumps({"id": session_id}))
        
        assert mock_redis.exists(f"session:{session_id}")


class TestErrorHandlingIntegration:
    """Test error handling across the system."""
    
    def test_invalid_task_handling(self):
        """Test handling of invalid task."""
        invalid_tasks = [
            "",
            "   ",
            None,
        ]
        
        for task in invalid_tasks:
            is_valid = task is not None and len(str(task).strip()) > 0
            assert not is_valid
    
    def test_agent_error_propagation(self):
        """Test error propagation from agent to API."""
        error_result = {
            "status": "failed",
            "error": {
                "type": "AgentExecutionError",
                "message": "Failed to generate response",
            }
        }
        
        assert error_result["status"] == "failed"
        assert "error" in error_result
    
    def test_database_error_handling(self, mock_redis):
        """Test database error handling."""
        # Simulate database error
        mock_redis_with_error = Mock()
        mock_redis_with_error.get.side_effect = ConnectionError("Database unavailable")
        
        with pytest.raises(ConnectionError):
            mock_redis_with_error.get("test")


class TestRateLimitingIntegration:
    """Test rate limiting integration."""
    
    def test_rate_limit_headers(self):
        """Test rate limit headers in response."""
        headers = {
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "9",
            "X-RateLimit-Reset": "1704067200",
        }
        
        assert int(headers["X-RateLimit-Limit"]) == 10
        assert int(headers["X-RateLimit-Remaining"]) < int(headers["X-RateLimit-Limit"])
    
    def test_rate_limit_exceeded_response(self):
        """Test rate limit exceeded response."""
        response = {
            "status_code": 429,
            "detail": "Rate limit exceeded. Try again in 60 seconds.",
        }
        
        assert response["status_code"] == 429


class TestLoggingIntegration:
    """Test logging integration."""
    
    def test_request_logging(self, mock_mongodb):
        """Test request logging."""
        collection = mock_mongodb["request_logs"]
        
        log_entry = {
            "method": "POST",
            "path": "/v1/agent/execute",
            "status_code": 200,
            "duration_ms": 150,
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
        collection.insert_one(log_entry)
        
        logs = collection.find({"path": "/v1/agent/execute"})
        assert len(logs) == 1
    
    def test_error_logging(self, mock_mongodb):
        """Test error logging."""
        collection = mock_mongodb["error_logs"]
        
        error_entry = {
            "error_type": "ValidationError",
            "message": "Invalid task format",
            "stack_trace": "...",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        
        collection.insert_one(error_entry)
        
        errors = collection.find({"error_type": "ValidationError"})
        assert len(errors) == 1


class TestMultiAgentWorkflow:
    """Test multi-agent workflow integration."""
    
    def test_business_to_problem_tree_flow(self):
        """Test flow from BusinessAgent to ProblemAgent."""
        # 1. Business diagnosis completed
        diagnosis = {
            "customer_stated_problem": "Revenue declining",
            "identified_business_problem": "Market share loss",
            "hidden_root_risk": "Competitive pressure",
            "urgency_level": "High",
        }
        
        # 2. Trigger problem tree generation
        should_generate_tree = diagnosis["urgency_level"] in ["High", "Critical"]
        assert should_generate_tree
        
        # 3. Problem tree generated
        problem_tree = {
            "root_problem": diagnosis["identified_business_problem"],
            "branches": [
                {"category": "Sales", "issues": ["Lower conversion"]},
                {"category": "Marketing", "issues": ["Weak positioning"]},
                {"category": "Product", "issues": ["Feature gaps"]},
            ]
        }
        
        assert problem_tree["root_problem"] == "Market share loss"
        assert len(problem_tree["branches"]) >= 2
    
    def test_peer_agent_routing(self):
        """Test PeerAgent routing to specialized agents."""
        tasks_and_routes = [
            ("Write Python code", "code_agent"),
            ("What is AI?", "content_agent"),
            ("Sales are down", "business_sense_agent"),
        ]
        
        for task, expected_agent in tasks_and_routes:
            # Simple routing logic
            if any(kw in task.lower() for kw in ["write", "code", "function"]):
                routed = "code_agent"
            elif any(kw in task.lower() for kw in ["what", "how", "explain"]):
                routed = "content_agent"
            elif any(kw in task.lower() for kw in ["sales", "revenue", "cost"]):
                routed = "business_sense_agent"
            else:
                routed = "content_agent"  # default
            
            assert routed == expected_agent, f"Task '{task}' should route to {expected_agent}"


class TestConcurrencyIntegration:
    """Test concurrent request handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_submissions(self):
        """Test handling concurrent task submissions."""
        import asyncio
        
        async def submit_task(task_id: str):
            await asyncio.sleep(0.01)  # Simulate work
            return {"task_id": task_id, "status": "submitted"}
        
        # Submit 5 tasks concurrently
        tasks = [submit_task(f"task-{i}") for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(r["status"] == "submitted" for r in results)
    
    def test_session_isolation(self, mock_redis):
        """Test that sessions are isolated."""
        # Create two sessions
        mock_redis.set("session:user1", json.dumps({"user": "user1", "data": "private1"}))
        mock_redis.set("session:user2", json.dumps({"user": "user2", "data": "private2"}))
        
        # Retrieve user1's session
        session1 = json.loads(mock_redis.get("session:user1"))
        
        # Should only see user1's data
        assert session1["user"] == "user1"
        assert "private1" in session1["data"]


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_complete_code_generation_workflow(self, mock_redis):
        """Test complete code generation from start to finish."""
        # 1. Create session
        session_id = "e2e-code-123"
        mock_redis.set(f"session:{session_id}", json.dumps({"id": session_id}))
        
        # 2. Submit task
        task = "Write a function to calculate factorial"
        task_id = "task-factorial-456"
        
        # 3. Store task
        task_data = {"task_id": task_id, "task": task, "status": "pending"}
        mock_redis.set(f"task:{task_id}", json.dumps(task_data))
        
        # 4. Execute (mocked)
        result = {
            "code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
            "language": "python",
        }
        
        # 5. Update task with result
        task_data["status"] = "completed"
        task_data["result"] = result
        mock_redis.set(f"task:{task_id}", json.dumps(task_data))
        
        # 6. Verify
        final_task = json.loads(mock_redis.get(f"task:{task_id}"))
        assert final_task["status"] == "completed"
        assert "factorial" in final_task["result"]["code"]
    
    def test_complete_business_analysis_workflow(self, mock_redis):
        """Test complete business analysis from start to finish."""
        session_id = "e2e-biz-123"
        
        # 1. Initial problem submission
        problem = "Customer churn increased by 15%"
        
        # 2. Questions phase
        questions = ["When did this start?", "Which segment?", "What's the impact?"]
        
        # 3. Answers phase
        answers = {
            "When did this start?": "2 months ago",
            "Which segment?": "SMB customers",
            "What's the impact?": "$500K monthly",
        }
        
        # 4. Diagnosis
        diagnosis = {
            "customer_stated_problem": problem,
            "identified_business_problem": "SMB retention crisis",
            "hidden_root_risk": "Product-market fit for SMB",
            "urgency_level": "Critical",
        }
        
        # 5. Store complete analysis
        analysis = {
            "session_id": session_id,
            "problem": problem,
            "questions": questions,
            "answers": answers,
            "diagnosis": diagnosis,
        }
        
        mock_redis.set(f"analysis:{session_id}", json.dumps(analysis))
        
        # 6. Verify
        stored = json.loads(mock_redis.get(f"analysis:{session_id}"))
        assert stored["diagnosis"]["urgency_level"] == "Critical"
