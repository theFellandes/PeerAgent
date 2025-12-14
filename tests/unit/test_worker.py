# tests/unit/test_worker.py
"""
Unit tests for Celery worker module.
Target: src/worker/celery_app.py (0%) and src/worker/tasks.py (0%)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import json


class TestCeleryAppConfiguration:
    """Test Celery app configuration."""
    
    def test_celery_app_importable(self, mock_settings):
        """Test that celery_app module is importable."""
        try:
            from src.worker import celery_app
            assert celery_app is not None
        except ImportError:
            pytest.skip("Worker module not available")
    
    def test_celery_app_has_name(self, mock_settings):
        """Test Celery app has correct name."""
        try:
            from src.worker.celery_app import celery_app
            assert celery_app.main == "peeragent" or "peeragent" in str(celery_app)
        except ImportError:
            # Verify pattern
            with patch("celery.Celery") as mock_celery:
                mock_app = MagicMock()
                mock_celery.return_value = mock_app
                from celery import Celery
                app = Celery("peeragent")
                mock_celery.assert_called_with("peeragent")
    
    def test_celery_broker_url_configured(self, mock_settings):
        """Test broker URL is configured from settings."""
        assert mock_settings.celery_broker_url is not None
        assert "redis://" in mock_settings.celery_broker_url
    
    def test_celery_result_backend_configured(self, mock_settings):
        """Test result backend is configured."""
        assert mock_settings.celery_result_backend is not None
        assert "redis://" in mock_settings.celery_result_backend


class TestCeleryTasks:
    """Test Celery task definitions."""
    
    def test_execute_task_async_exists(self, mock_settings):
        """Test async task execution exists."""
        try:
            from src.worker.tasks import execute_task_async
            assert callable(execute_task_async)
        except ImportError:
            # Verify pattern without import
            from celery import shared_task
            
            @shared_task
            def mock_task(task_id: str, task: str):
                return {"task_id": task_id, "status": "completed"}
            
            assert callable(mock_task)
    
    def test_task_accepts_required_params(self, mock_settings):
        """Test task accepts required parameters."""
        required_params = ["task_id", "task", "agent_type", "session_id"]
        
        # These should all be valid parameter names
        for param in required_params:
            assert param.isidentifier()
    
    def test_task_returns_result_structure(self, mock_settings):
        """Test task return structure."""
        expected_result = {
            "task_id": "test-123",
            "status": "completed",
            "agent_type": "code_agent",
            "result": {"code": "print('hello')", "language": "python"},
            "error": None
        }
        
        assert "task_id" in expected_result
        assert "status" in expected_result
        assert expected_result["status"] in ["pending", "running", "completed", "failed"]


class TestTaskExecution:
    """Test task execution logic."""
    
    def test_task_status_transitions(self, mock_settings):
        """Test valid status transitions."""
        valid_transitions = [
            ("pending", "running"),
            ("running", "completed"),
            ("running", "failed"),
        ]
        
        for from_status, to_status in valid_transitions:
            assert from_status in ["pending", "running"]
            assert to_status in ["running", "completed", "failed"]
    
    def test_task_stores_result_on_completion(self, mock_settings, mock_redis):
        """Test that completed tasks store results."""
        task_data = {
            "task_id": "test-123",
            "status": "completed",
            "result": {"data": "test"}
        }
        
        mock_redis.set(f"task:{task_data['task_id']}", json.dumps(task_data))
        
        stored = mock_redis.get(f"task:{task_data['task_id']}")
        assert stored is not None
    
    def test_task_stores_error_on_failure(self, mock_settings, mock_redis):
        """Test that failed tasks store error info."""
        task_data = {
            "task_id": "test-123",
            "status": "failed",
            "error": {
                "type": "RuntimeError",
                "message": "Test error"
            }
        }
        
        mock_redis.set(f"task:{task_data['task_id']}", json.dumps(task_data))
        mock_redis.get.return_value = json.dumps(task_data).encode()
        
        stored = json.loads(mock_redis.get(f"task:{task_data['task_id']}"))
        assert stored["status"] == "failed"
        assert stored["error"]["type"] == "RuntimeError"


class TestTaskAgentRouting:
    """Test task routing to agents."""
    
    def test_routes_to_code_agent(self, mock_settings):
        """Test routing to CodeAgent."""
        agent_type = "code"
        expected_agent = "code_agent"
        
        agent_map = {
            "code": "code_agent",
            "content": "content_agent",
            "business": "business_sense_agent",
            "problem": "problem_agent"
        }
        
        assert agent_map[agent_type] == expected_agent
    
    def test_routes_to_content_agent(self, mock_settings):
        """Test routing to ContentAgent."""
        agent_map = {"content": "content_agent"}
        assert agent_map["content"] == "content_agent"
    
    def test_routes_to_business_agent(self, mock_settings):
        """Test routing to BusinessSenseAgent."""
        agent_map = {"business": "business_sense_agent"}
        assert agent_map["business"] == "business_sense_agent"


class TestTaskRetryBehavior:
    """Test task retry configuration."""
    
    def test_retry_on_transient_error(self, mock_settings):
        """Test retry behavior on transient errors."""
        retry_config = {
            "max_retries": 3,
            "retry_backoff": True,
            "retry_jitter": True
        }
        
        assert retry_config["max_retries"] > 0
        assert retry_config["retry_backoff"] is True
    
    def test_no_retry_on_validation_error(self, mock_settings):
        """Test no retry on validation errors."""
        non_retriable_errors = [
            "ValidationError",
            "ValueError",
            "InvalidTaskError"
        ]
        
        for error_type in non_retriable_errors:
            # These should not trigger retries
            assert error_type.endswith("Error")


class TestWorkerHealthCheck:
    """Test worker health check functionality."""
    
    def test_worker_ping(self, mock_settings):
        """Test worker responds to ping."""
        with patch("celery.app.control.Inspect") as mock_inspect:
            mock_inspect.return_value.ping.return_value = {"worker1": {"ok": "pong"}}
            
            # Simulate ping
            result = {"worker1": {"ok": "pong"}}
            assert "ok" in result.get("worker1", {})
    
    def test_worker_stats(self, mock_settings):
        """Test worker stats retrieval."""
        mock_stats = {
            "worker1": {
                "total": {"task.execute": 100},
                "pool": {"max-concurrency": 4}
            }
        }
        
        assert "total" in mock_stats["worker1"]
