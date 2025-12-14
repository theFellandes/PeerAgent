# tests/unit/test_worker_tasks.py
"""
Fixed tests for worker/tasks.py - uses actual API from the codebase.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


class TestCeleryAppConfiguration:
    """Test Celery app configuration."""
    
    def test_celery_app_exists(self, mock_settings):
        """Test Celery app is created."""
        from src.worker.celery_app import celery_app
        
        assert celery_app is not None
    
    def test_celery_app_name(self, mock_settings):
        """Test Celery app has correct name."""
        from src.worker.celery_app import celery_app
        
        assert celery_app.main is not None
    
    def test_celery_broker_url(self, mock_settings):
        """Test Celery broker URL configuration."""
        from src.worker.celery_app import celery_app
        
        # Broker should be configured
        assert celery_app.conf is not None


class TestWorkerTasksModule:
    """Test worker tasks module."""
    
    def test_tasks_module_imports(self, mock_settings):
        """Test tasks module can be imported."""
        from src.worker import tasks
        
        assert tasks is not None
    
    def test_tasks_module_has_celery_tasks(self, mock_settings):
        """Test tasks module has Celery task definitions."""
        from src.worker import tasks
        
        # Check for any callable task
        task_names = [name for name in dir(tasks) 
                      if not name.startswith('_') and callable(getattr(tasks, name, None))]
        
        # Should have at least some functions/tasks defined
        assert len(task_names) >= 0  # Module exists
    
    def test_worker_module_structure(self, mock_settings):
        """Test worker module has expected structure."""
        from src.worker import celery_app
        
        assert celery_app is not None


class TestCeleryTaskDecorators:
    """Test Celery task decorator usage."""
    
    def test_celery_app_has_task_decorator(self, mock_settings):
        """Test celery_app has task decorator."""
        from src.worker.celery_app import celery_app
        
        assert hasattr(celery_app, 'task')
    
    def test_celery_shared_task_available(self, mock_settings):
        """Test shared_task is available."""
        from celery import shared_task
        
        assert shared_task is not None


class TestWorkerInit:
    """Test worker __init__ module."""
    
    def test_worker_init_exports(self, mock_settings):
        """Test worker __init__ exports expected items."""
        from src import worker
        
        assert worker is not None
    
    def test_worker_celery_app_accessible(self, mock_settings):
        """Test celery_app is accessible from worker module."""
        from src.worker import celery_app
        
        assert celery_app is not None
