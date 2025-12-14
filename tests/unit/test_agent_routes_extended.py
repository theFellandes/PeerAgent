# tests/unit/test_agent_routes_extended.py
"""
Extended tests for agent routes to increase coverage from 32% to 60%+.
Target lines: 45, 92-161, 192-236, 270, 298-307, 328-337, 383-433, 451-499, 516-521, 537-538
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
import json


class TestExecuteEndpointExtended:
    """Extended tests for /v1/agent/execute endpoint."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_execute_with_session_id(self, client, mock_settings):
        """Test execute with custom session ID."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/execute",
                json={
                    "task": "Write Python code",
                    "session_id": "custom-session-123"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
    
    def test_execute_returns_processing_status(self, client, mock_settings):
        """Test execute returns task status."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/execute",
                json={"task": "Write code"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["pending", "processing", "completed"]
    
    def test_execute_long_task(self, client, mock_settings):
        """Test execute with long task description."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance
            
            long_task = "Write a comprehensive Python function that " * 10
            
            response = client.post(
                "/v1/agent/execute",
                json={"task": long_task}
            )
            
            assert response.status_code == 200


class TestDirectAgentEndpointExtended:
    """Extended tests for /v1/agent/execute/direct/{agent_type}."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_direct_code_agent(self, client, mock_settings):
        """Test direct code agent execution."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute_with_agent_type = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "def test(): pass", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/execute/direct/code",
                json={"task": "Write a function"}
            )
            
            assert response.status_code == 200
    
    def test_direct_content_agent(self, client, mock_settings):
        """Test direct content agent execution."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute_with_agent_type = AsyncMock(return_value={
                "agent_type": "content_agent",
                "data": {"content": "Information", "sources": []}
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/execute/direct/content",
                json={"task": "What is AI?"}
            )
            
            assert response.status_code == 200
    
    def test_direct_business_agent(self, client, mock_settings):
        """Test direct business agent execution."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute_with_agent_type = AsyncMock(return_value={
                "agent_type": "business_sense_agent",
                "data": {"type": "questions", "questions": ["Q1?"]}
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/execute/direct/business",
                json={"task": "Sales dropped 20%"}
            )
            
            assert response.status_code == 200
    
    def test_direct_invalid_agent_type(self, client, mock_settings):
        """Test direct with invalid agent type."""
        response = client.post(
            "/v1/agent/execute/direct/invalid_type",
            json={"task": "Test"}
        )
        
        assert response.status_code == 400
        assert "INVALID_AGENT_TYPE" in response.text


class TestStatusEndpointExtended:
    """Extended tests for /v1/agent/status/{task_id}."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_status_completed_task(self, client, mock_settings):
        """Test status of completed task."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance
            
            # Create task first
            execute_response = client.post(
                "/v1/agent/execute",
                json={"task": "Write code"}
            )
            task_id = execute_response.json()["task_id"]
            
            # Get status
            status_response = client.get(f"/v1/agent/status/{task_id}")
            
            assert status_response.status_code == 200
            data = status_response.json()
            assert data["task_id"] == task_id
    
    def test_status_nonexistent_task(self, client, mock_settings):
        """Test status of non-existent task."""
        response = client.get("/v1/agent/status/nonexistent-task-12345")
        
        assert response.status_code == 404
        assert "TASK_NOT_FOUND" in response.text


class TestClassifyEndpointExtended:
    """Extended tests for /v1/agent/classify endpoint."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_classify_code_task(self, client, mock_settings):
        """Test classification of code task."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.classify_task = AsyncMock(return_value="code")
            MockAgent.return_value = mock_instance
            
            response = client.get("/v1/agent/classify?task=Write%20Python%20code")
            
            assert response.status_code == 200
            data = response.json()
            assert data["classification"] == "code"
    
    def test_classify_content_task(self, client, mock_settings):
        """Test classification of content task."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.classify_task = AsyncMock(return_value="content")
            MockAgent.return_value = mock_instance
            
            response = client.get("/v1/agent/classify?task=What%20is%20AI")
            
            assert response.status_code == 200
    
    def test_classify_business_task(self, client, mock_settings):
        """Test classification of business task."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.classify_task = AsyncMock(return_value="business")
            MockAgent.return_value = mock_instance
            
            response = client.get("/v1/agent/classify?task=Sales%20dropped")
            
            assert response.status_code == 200
    
    def test_classify_empty_task(self, client, mock_settings):
        """Test classification with empty task."""
        response = client.get("/v1/agent/classify?task=")
        
        assert response.status_code == 400


class TestTaskListEndpoint:
    """Tests for /v1/agent/tasks endpoint."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_list_tasks(self, client, mock_settings):
        """Test listing all tasks."""
        response = client.get("/v1/agent/tasks")
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_list_tasks_with_limit(self, client, mock_settings):
        """Test listing tasks with limit."""
        response = client.get("/v1/agent/tasks?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
    
    def test_list_tasks_by_session(self, client, mock_settings):
        """Test listing tasks by session."""
        response = client.get("/v1/agent/tasks?session_id=test-session")
        
        assert response.status_code == 200


class TestBusinessContinueEndpoint:
    """Tests for /v1/agent/business/continue endpoint."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_business_continue_with_answers(self, client, mock_settings):
        """Test continuing business conversation with answers."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.business_agent = Mock()
            mock_instance.business_agent.continue_with_answers = AsyncMock(return_value={
                "type": "diagnosis",
                "data": {
                    "customer_stated_problem": "Test",
                    "identified_business_problem": "Test",
                    "hidden_root_risk": "Test",
                    "urgency_level": "Medium"
                }
            })
            MockAgent.return_value = mock_instance
            
            response = client.post(
                "/v1/agent/business/continue",
                json={
                    "session_id": "test-session",
                    "answers": {"Q1": "A1", "Q2": "A2"}
                }
            )
            
            assert response.status_code == 200


class TestValidationErrors:
    """Test validation error handling."""
    
    @pytest.fixture
    def client(self, mock_settings):
        from src.api.main import create_app
        app = create_app()
        return TestClient(app)
    
    def test_execute_missing_task(self, client, mock_settings):
        """Test execute without task field."""
        response = client.post(
            "/v1/agent/execute",
            json={}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_execute_invalid_json(self, client, mock_settings):
        """Test execute with invalid JSON."""
        response = client.post(
            "/v1/agent/execute",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_direct_missing_task(self, client, mock_settings):
        """Test direct agent without task."""
        response = client.post(
            "/v1/agent/execute/direct/code",
            json={}
        )
        
        assert response.status_code == 422
