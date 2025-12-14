# Comprehensive Integration Tests
"""
Integration tests covering:
- Full API workflow testing
- Redis task store operations
- WebSocket communication
- Agent execution flow
- Error handling scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import json


# =============================================================================
# API Integration Tests
# =============================================================================

class TestAPIWorkflow:
    """Test complete API workflows from request to response."""
    
    @pytest.fixture
    def client(self, mock_settings):
        """Create test client for the FastAPI app."""
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_complete_code_workflow(self, client, mock_settings):
        """Test complete workflow: submit code task -> get status -> verify result."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {
                    "code": "def hello(): return 'Hello World'",
                    "language": "python",
                    "explanation": "A simple function"
                }
            })
            MockAgent.return_value = mock_instance
            
            # Step 1: Submit task
            response = client.post(
                "/v1/agent/execute",
                json={"task": "Write a hello world function in Python"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            task_id = data["task_id"]
            
            # Step 2: Check status
            status_response = client.get(f"/v1/agent/status/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["task_id"] == task_id
            assert status_data["status"] in ["completed", "processing", "pending"]
    
    def test_complete_business_workflow(self, client, mock_settings):
        """Test business analysis workflow with questions and continuation."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            # First call returns questions
            mock_instance = Mock()
            mock_business = Mock()
            mock_business.execute = AsyncMock(return_value={
                "type": "questions",
                "data": {
                    "session_id": "test-session",
                    "questions": [
                        "When did this problem start?",
                        "What is the measurable impact?"
                    ],
                    "category": "problem_identification"
                }
            })
            mock_instance.business_agent = mock_business
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "business_sense_agent",
                "data": {
                    "type": "questions",
                    "questions": ["When did this start?"]
                }
            })
            MockAgent.return_value = mock_instance
            
            # Step 1: Submit business problem
            response = client.post(
                "/v1/agent/execute/direct/business",
                json={
                    "task": "Our sales dropped 20% this quarter",
                    "session_id": "test-session"
                }
            )
            assert response.status_code == 200
            
            # Step 2: Continue with answers (diagnosis)
            mock_business.execute = AsyncMock(return_value={
                "type": "diagnosis",
                "data": {
                    "customer_stated_problem": "Sales dropped 20%",
                    "identified_business_problem": "Market share loss",
                    "hidden_root_risk": "Brand degradation",
                    "urgency_level": "Critical"
                }
            })
            
            continue_response = client.post(
                "/v1/agent/business/continue",
                json={
                    "session_id": "test-session",
                    "answers": {
                        "When did this start?": "3 months ago",
                        "What is the impact?": "$2M revenue loss"
                    }
                }
            )
            assert continue_response.status_code == 200
    
    def test_error_handling_workflow(self, client, mock_settings):
        """Test error handling throughout the workflow."""
        # Test empty task
        response = client.post(
            "/v1/agent/execute",
            json={"task": ""}
        )
        assert response.status_code in [400, 422]
        
        # Test whitespace-only task
        response = client.post(
            "/v1/agent/execute",
            json={"task": "   "}
        )
        assert response.status_code == 400
        
        # Test invalid agent type
        response = client.post(
            "/v1/agent/execute/direct/invalid",
            json={"task": "Test"}
        )
        assert response.status_code == 400
        assert "INVALID_AGENT_TYPE" in str(response.json())
        
        # Test non-existent task
        response = client.get("/v1/agent/status/nonexistent-task-id")
        assert response.status_code == 404
        assert "TASK_NOT_FOUND" in str(response.json())


class TestTaskListingAndFiltering:
    """Test task listing and filtering functionality."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_list_tasks_empty(self, client, mock_settings):
        """Test listing tasks when none exist."""
        response = client.get("/v1/agent/tasks")
        assert response.status_code == 200
        # Should return empty list or existing tasks
        assert isinstance(response.json(), list)
    
    def test_list_tasks_with_limit(self, client, mock_settings):
        """Test listing tasks with limit parameter."""
        response = client.get("/v1/agent/tasks?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
    
    def test_list_tasks_by_session(self, client, mock_settings):
        """Test listing tasks filtered by session."""
        response = client.get("/v1/agent/tasks?session_id=test-session")
        assert response.status_code == 200


# =============================================================================
# Redis Task Store Integration Tests
# =============================================================================

class TestRedisTaskStore:
    """Test Redis task store operations."""
    
    @pytest.fixture
    def task_store(self, mock_settings):
        """Get task store instance (may fall back to in-memory)."""
        from src.utils.task_store import get_task_store, TaskData, TaskStatus
        return get_task_store()
    
    @pytest.fixture
    def sample_task(self):
        from src.utils.task_store import TaskData, TaskStatus
        return TaskData(
            task_id="test-task-123",
            status=TaskStatus.PENDING,
            task="Test task",
            session_id="test-session"
        )
    
    def test_create_and_get_task(self, task_store, sample_task):
        """Test creating and retrieving a task."""
        # Create
        created = task_store.create(sample_task)
        assert created.task_id == sample_task.task_id
        
        # Get
        retrieved = task_store.get(sample_task.task_id)
        assert retrieved is not None
        assert retrieved.task_id == sample_task.task_id
        assert retrieved.task == sample_task.task
        
        # Cleanup
        task_store.delete(sample_task.task_id)
    
    def test_update_task(self, task_store, sample_task):
        """Test updating a task."""
        from src.utils.task_store import TaskStatus
        
        task_store.create(sample_task)
        
        # Update
        updated = task_store.update(sample_task.task_id, {
            "status": TaskStatus.COMPLETED,
            "result": {"data": "test result"}
        })
        
        assert updated is not None
        assert updated.status == TaskStatus.COMPLETED
        assert updated.result == {"data": "test result"}
        
        # Cleanup
        task_store.delete(sample_task.task_id)
    
    def test_delete_task(self, task_store, sample_task):
        """Test deleting a task."""
        task_store.create(sample_task)
        
        # Delete
        result = task_store.delete(sample_task.task_id)
        assert result is True
        
        # Verify deleted
        assert task_store.get(sample_task.task_id) is None
    
    def test_task_not_found(self, task_store):
        """Test handling non-existent task."""
        result = task_store.get("nonexistent-task")
        assert result is None
    
    def test_list_tasks(self, task_store):
        """Test listing tasks."""
        from src.utils.task_store import TaskData, TaskStatus
        
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            task = TaskData(
                task_id=f"test-list-{i}",
                status=TaskStatus.COMPLETED,
                task=f"Test task {i}",
                session_id="test-session"
            )
            task_store.create(task)
            task_ids.append(task.task_id)
        
        # List
        tasks = task_store.list_tasks(limit=10)
        assert len(tasks) >= 3
        
        # Cleanup
        for tid in task_ids:
            task_store.delete(tid)


# =============================================================================
# Agent Classification Tests
# =============================================================================

class TestClassificationIntegration:
    """Test task classification with real routing logic."""
    
    @pytest.fixture
    def peer_agent(self, mock_settings):
        from src.agents.peer_agent import PeerAgent
        return PeerAgent()
    
    @pytest.mark.asyncio
    async def test_code_task_classification(self, peer_agent, mock_settings):
        """Test that code tasks are classified correctly."""
        code_tasks = [
            "Write a Python function to sort a list",
            "Create a SQL query to find customers",
            "Debug this JavaScript code",
            "Implement a REST API endpoint in Java"
        ]
        
        for task in code_tasks:
            result = peer_agent._keyword_classify(task)
            assert result == "code", f"'{task}' should be classified as code"
    
    @pytest.mark.asyncio
    async def test_business_task_classification(self, peer_agent, mock_settings):
        """Test that business tasks are classified correctly."""
        business_tasks = [
            "Our sales are dropping and revenue is declining",
            "Customer churn has increased significantly",
            "Diagnose our operational efficiency problems"
        ]
        
        for task in business_tasks:
            result = peer_agent._keyword_classify(task)
            assert result == "business", f"'{task}' should be classified as business"
    
    @pytest.mark.asyncio
    async def test_content_task_classification(self, peer_agent, mock_settings):
        """Test that content tasks are classified correctly."""
        content_tasks = [
            "What is machine learning? Explain it to me",
            "Search for information about climate change",
            "Research the latest AI news"
        ]
        
        for task in content_tasks:
            result = peer_agent._keyword_classify(task)
            assert result == "content", f"'{task}' should be classified as content"


# =============================================================================
# WebSocket Integration Tests
# =============================================================================

class TestWebSocketIntegration:
    """Test WebSocket functionality."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_websocket_connection(self, client, mock_settings):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/ws/agent/test-session") as websocket:
            # Should receive acknowledgment
            data = websocket.receive_json()
            assert data["type"] == "ack"
            assert "session_id" in data
    
    def test_websocket_ping_pong(self, client, mock_settings):
        """Test WebSocket ping/pong."""
        with client.websocket_connect("/ws/agent/test-session") as websocket:
            # Skip ack
            websocket.receive_json()
            
            # Send ping
            websocket.send_json({
                "type": "ping",
                "data": {}
            })
            
            # Receive pong
            response = websocket.receive_json()
            assert response["type"] == "pong"
    
    def test_websocket_invalid_message(self, client, mock_settings):
        """Test WebSocket error handling for invalid messages."""
        with client.websocket_connect("/ws/agent/test-session") as websocket:
            # Skip ack
            websocket.receive_json()
            
            # Send invalid message
            websocket.send_text("invalid json")
            
            # Should receive error
            response = websocket.receive_json()
            assert response["type"] == "error"


# =============================================================================
# Rate Limiting Integration Tests
# =============================================================================

class TestRateLimitingIntegration:
    """Test rate limiting across multiple requests."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_health_not_rate_limited(self, client, mock_settings):
        """Test that health endpoint is not rate limited."""
        for _ in range(20):
            response = client.get("/health")
            assert response.status_code == 200
    
    def test_ping_not_rate_limited(self, client, mock_settings):
        """Test that ping endpoint is not rate limited."""
        for _ in range(20):
            response = client.get("/ping")
            assert response.status_code == 200


# =============================================================================
# Memory Integration Tests
# =============================================================================

class TestMemoryIntegration:
    """Test memory/session management integration."""
    
    def test_memory_store_singleton(self, mock_settings):
        """Test that memory store is a singleton."""
        from src.utils.memory import get_memory_store
        
        store1 = get_memory_store()
        store2 = get_memory_store()
        
        assert store1 is store2
    
    def test_session_persistence(self, mock_settings):
        """Test that session data persists across calls."""
        from src.utils.memory import get_memory_store
        
        memory = get_memory_store()
        session_id = "test-persistence-session"
        
        # Clear any existing
        memory.clear_session(session_id)
        
        # Add interactions
        memory.add_interaction(session_id, "Hello", "Hi there!")
        memory.add_interaction(session_id, "How are you?", "I'm doing well!")
        
        # Retrieve
        messages = memory.get_messages(session_id)
        assert len(messages) == 4  # 2 interactions = 4 messages (human + AI each)
        
        # Cleanup
        memory.clear_session(session_id)


# =============================================================================
# Full End-to-End Tests
# =============================================================================

class TestEndToEnd:
    """End-to-end tests simulating real user workflows."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_e2e_multi_agent_session(self, client, mock_settings):
        """Test a session using multiple agents."""
        session_id = "e2e-test-session"
        
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            
            # Configure code agent response
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {
                    "code": "def sort_list(lst): return sorted(lst)",
                    "language": "python",
                    "explanation": "Uses built-in sorted function"
                }
            })
            mock_instance.execute_with_agent_type = AsyncMock(return_value={
                "agent_type": "content_agent",
                "data": {
                    "content": "Python is a programming language...",
                    "sources": ["https://python.org"]
                }
            })
            MockAgent.return_value = mock_instance
            
            # Execute code task
            code_response = client.post(
                "/v1/agent/execute",
                json={
                    "task": "Write a Python function to sort a list",
                    "session_id": session_id
                }
            )
            assert code_response.status_code == 200
            
            # Execute content task in same session
            content_response = client.post(
                "/v1/agent/execute/direct/content",
                json={
                    "task": "Tell me about Python",
                    "session_id": session_id
                }
            )
            assert content_response.status_code == 200
    
    def test_e2e_api_info_endpoints(self, client, mock_settings):
        """Test all informational endpoints."""
        # Root
        response = client.get("/")
        assert response.status_code == 200
        assert "version" in response.json()
        
        # Health
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()
        
        # Ping
        response = client.get("/ping")
        assert response.status_code == 200
        
        # API Info
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "endpoints" in data
        assert "agent_types" in data
