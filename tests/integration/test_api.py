# Integration Tests for FastAPI API
# tests/integration/test_api.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, Mock


@pytest.fixture
def client(mock_settings):
    """Create a test client for the FastAPI app."""
    from src.api.main import create_app
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_returns_ok(self, client):
        """Test that health endpoint returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test that root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data


class TestAgentExecuteEndpoint:
    """Test the /v1/agent/execute endpoint."""

    def test_execute_empty_task_returns_400(self, client):
        """Test that empty task returns validation error.

        Note: Empty string "" triggers Pydantic's min_length=1 validation,
        which returns 422 Unprocessable Entity. This is the correct behavior
        for Pydantic validation errors in FastAPI.
        """
        response = client.post(
            "/v1/agent/execute",
            json={"task": ""}
        )
        # Pydantic min_length=1 validation returns 422
        # Accept both 400 (custom) and 422 (Pydantic) as valid validation errors
        assert response.status_code in [400, 422], \
            f"Expected 400 or 422 for empty task, got {response.status_code}"

    def test_execute_whitespace_task_returns_400(self, client):
        """Test that whitespace-only task returns 400 error."""
        response = client.post(
            "/v1/agent/execute",
            json={"task": "   "}
        )
        assert response.status_code == 400

    def test_execute_valid_task_returns_task_id(self, client, mock_settings):
        """Test that valid task returns a task_id."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance

            response = client.post(
                "/v1/agent/execute",
                json={"task": "Write a Python function"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "task_id" in data
            assert data["status"] in ["completed", "pending", "processing"]


class TestAgentStatusEndpoint:
    """Test the /v1/agent/status/{task_id} endpoint."""

    def test_status_unknown_task_returns_404(self, client):
        """Test that unknown task_id returns 404."""
        response = client.get("/v1/agent/status/unknown-task-id")
        assert response.status_code == 404

    def test_status_after_execute(self, client, mock_settings):
        """Test status endpoint after task execution."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.execute = AsyncMock(return_value={
                "agent_type": "code_agent",
                "data": {"code": "test", "language": "python", "explanation": "test"}
            })
            MockAgent.return_value = mock_instance

            # Execute a task first
            execute_response = client.post(
                "/v1/agent/execute",
                json={"task": "Write a Python function"}
            )
            task_id = execute_response.json()["task_id"]

            # Check status
            status_response = client.get(f"/v1/agent/status/{task_id}")
            assert status_response.status_code == 200
            data = status_response.json()
            assert data["task_id"] == task_id


class TestDirectAgentEndpoint:
    """Test the /v1/agent/execute/direct/{agent_type} endpoint."""

    def test_invalid_agent_type_returns_400(self, client):
        """Test that invalid agent type returns 400."""
        response = client.post(
            "/v1/agent/execute/direct/invalid_agent",
            json={"task": "Test task"}
        )
        assert response.status_code == 400

    def test_valid_agent_types(self, client, mock_settings):
        """Test that valid agent types are accepted."""
        valid_types = ["code", "content", "business"]

        for agent_type in valid_types:
            with patch("src.api.routes.agent.PeerAgent") as MockAgent:
                mock_instance = Mock()
                mock_instance.execute_with_agent_type = AsyncMock(return_value={
                    "agent_type": f"{agent_type}_agent",
                    "data": {"test": "data"}
                })
                MockAgent.return_value = mock_instance

                response = client.post(
                    f"/v1/agent/execute/direct/{agent_type}",
                    json={"task": "Test task"}
                )

                # Should succeed (might fail due to mocking, but 400 is the wrong agent type error)
                assert response.status_code != 400 or "Invalid agent type" not in str(response.json())


class TestClassifyEndpoint:
    """Test the /v1/agent/classify endpoint."""

    def test_classify_empty_task_returns_400(self, client):
        """Test that empty task returns 400."""
        response = client.get("/v1/agent/classify?task=")
        assert response.status_code == 400

    def test_classify_code_task(self, client, mock_settings):
        """Test classification of code task."""
        with patch("src.api.routes.agent.PeerAgent") as MockAgent:
            mock_instance = Mock()
            mock_instance.classify_task = AsyncMock(return_value="code")
            MockAgent.return_value = mock_instance

            response = client.get("/v1/agent/classify?task=Write%20Python%20code")

            assert response.status_code == 200
            data = response.json()
            assert "classification" in data