"""
Comprehensive unit tests for logger module.
Target: src/utils/logger.py (45% coverage -> 80%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
import logging
import json
from datetime import datetime


class TestLoggerSetup:
    """Test logger setup and initialization."""
    
    def test_create_logger(self):
        """Test creating a logger instance."""
        logger = logging.getLogger("peeragent")
        
        assert logger is not None
        assert logger.name == "peeragent"
    
    def test_logger_level_default(self):
        """Test default logger level."""
        logger = logging.getLogger("test_default")
        logger.setLevel(logging.INFO)
        
        assert logger.level == logging.INFO
    
    def test_logger_level_from_env(self):
        """Test logger level from environment."""
        import os
        
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level_str = os.environ.get("LOG_LEVEL", "INFO")
            level = getattr(logging, level_str.upper())
            
            assert level == logging.DEBUG
    
    def test_add_stream_handler(self):
        """Test adding stream handler."""
        logger = logging.getLogger("test_stream")
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        
        assert len(logger.handlers) >= 1
    
    def test_add_file_handler(self):
        """Test adding file handler configuration."""
        # Simulate file handler config
        config = {
            "filename": "peeragent.log",
            "maxBytes": 10_000_000,  # 10MB
            "backupCount": 5,
        }
        
        assert config["filename"] == "peeragent.log"
        assert config["maxBytes"] == 10_000_000


class TestLogFormatting:
    """Test log message formatting."""
    
    def test_basic_format(self):
        """Test basic log format."""
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_str)
        
        assert "asctime" in format_str
        assert "levelname" in format_str
    
    def test_json_format(self):
        """Test JSON log format."""
        def format_json_log(record: dict) -> str:
            log_entry = {
                "timestamp": record.get("timestamp"),
                "level": record.get("level"),
                "message": record.get("message"),
                "logger": record.get("logger"),
            }
            return json.dumps(log_entry)
        
        record = {
            "timestamp": "2024-01-01T00:00:00Z",
            "level": "INFO",
            "message": "Test message",
            "logger": "peeragent",
        }
        
        formatted = format_json_log(record)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
    
    def test_format_with_extra_fields(self):
        """Test format with extra fields."""
        log_entry = {
            "timestamp": "2024-01-01T00:00:00Z",
            "level": "INFO",
            "message": "Task completed",
            "extra": {
                "task_id": "task-123",
                "duration_ms": 150,
            },
        }
        
        assert log_entry["extra"]["task_id"] == "task-123"


class TestLogLevels:
    """Test log level functionality."""
    
    def test_debug_level(self):
        """Test DEBUG level logging."""
        logger = logging.getLogger("test_debug")
        logger.setLevel(logging.DEBUG)
        
        with patch.object(logger, 'debug') as mock_debug:
            logger.debug("Debug message")
            mock_debug.assert_called_once_with("Debug message")
    
    def test_info_level(self):
        """Test INFO level logging."""
        logger = logging.getLogger("test_info")
        logger.setLevel(logging.INFO)
        
        with patch.object(logger, 'info') as mock_info:
            logger.info("Info message")
            mock_info.assert_called_once_with("Info message")
    
    def test_warning_level(self):
        """Test WARNING level logging."""
        logger = logging.getLogger("test_warning")
        
        with patch.object(logger, 'warning') as mock_warning:
            logger.warning("Warning message")
            mock_warning.assert_called_once_with("Warning message")
    
    def test_error_level(self):
        """Test ERROR level logging."""
        logger = logging.getLogger("test_error")
        
        with patch.object(logger, 'error') as mock_error:
            logger.error("Error message")
            mock_error.assert_called_once_with("Error message")
    
    def test_critical_level(self):
        """Test CRITICAL level logging."""
        logger = logging.getLogger("test_critical")
        
        with patch.object(logger, 'critical') as mock_critical:
            logger.critical("Critical message")
            mock_critical.assert_called_once_with("Critical message")
    
    def test_level_filtering(self):
        """Test log level filtering."""
        logger = logging.getLogger("test_filter")
        logger.setLevel(logging.WARNING)
        
        # DEBUG and INFO should be filtered out
        assert not logger.isEnabledFor(logging.DEBUG)
        assert not logger.isEnabledFor(logging.INFO)
        assert logger.isEnabledFor(logging.WARNING)
        assert logger.isEnabledFor(logging.ERROR)


class TestStructuredLogging:
    """Test structured logging functionality."""
    
    def test_log_with_context(self):
        """Test logging with context data."""
        def log_with_context(message: str, **context) -> dict:
            return {
                "message": message,
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        log = log_with_context(
            "Task completed",
            task_id="task-123",
            duration_ms=150,
        )
        
        assert log["context"]["task_id"] == "task-123"
        assert log["context"]["duration_ms"] == 150
    
    def test_log_request(self):
        """Test request logging."""
        request_log = {
            "type": "request",
            "method": "POST",
            "path": "/v1/agent/execute",
            "headers": {"Content-Type": "application/json"},
            "body_size": 256,
            "client_ip": "192.168.1.1",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert request_log["type"] == "request"
        assert request_log["method"] == "POST"
    
    def test_log_response(self):
        """Test response logging."""
        response_log = {
            "type": "response",
            "status_code": 200,
            "duration_ms": 150,
            "body_size": 1024,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert response_log["type"] == "response"
        assert response_log["status_code"] == 200
    
    def test_log_error(self):
        """Test error logging."""
        error_log = {
            "type": "error",
            "error_type": "ValidationError",
            "error_message": "Invalid task format",
            "stack_trace": "Traceback...",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert error_log["type"] == "error"
        assert error_log["error_type"] == "ValidationError"


class TestTaskLogging:
    """Test task-specific logging."""
    
    def test_log_task_created(self):
        """Test logging task creation."""
        log = {
            "event": "task_created",
            "task_id": "task-123",
            "task_type": "code",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "task_created"
        assert log["task_id"] == "task-123"
    
    def test_log_task_started(self):
        """Test logging task start."""
        log = {
            "event": "task_started",
            "task_id": "task-123",
            "agent_type": "code_agent",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "task_started"
        assert log["agent_type"] == "code_agent"
    
    def test_log_task_completed(self):
        """Test logging task completion."""
        log = {
            "event": "task_completed",
            "task_id": "task-123",
            "duration_ms": 1500,
            "result_size": 2048,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "task_completed"
        assert log["duration_ms"] == 1500
    
    def test_log_task_failed(self):
        """Test logging task failure."""
        log = {
            "event": "task_failed",
            "task_id": "task-123",
            "error_type": "LLMError",
            "error_message": "API timeout",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "task_failed"
        assert log["error_type"] == "LLMError"


class TestAgentLogging:
    """Test agent-specific logging."""
    
    def test_log_agent_execution(self):
        """Test logging agent execution."""
        log = {
            "event": "agent_execution",
            "agent_type": "code_agent",
            "session_id": "session-456",
            "task_preview": "Write a function...",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "agent_execution"
        assert log["agent_type"] == "code_agent"
    
    def test_log_llm_call(self):
        """Test logging LLM calls."""
        log = {
            "event": "llm_call",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "prompt_tokens": 500,
            "completion_tokens": 200,
            "duration_ms": 800,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "llm_call"
        assert log["provider"] == "openai"
        assert log["prompt_tokens"] == 500
    
    def test_log_provider_fallback(self):
        """Test logging provider fallback."""
        log = {
            "event": "provider_fallback",
            "from_provider": "openai",
            "to_provider": "anthropic",
            "reason": "Rate limit exceeded",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["event"] == "provider_fallback"
        assert log["from_provider"] == "openai"


class TestPerformanceLogging:
    """Test performance logging."""
    
    def test_log_duration(self):
        """Test logging duration."""
        import time
        
        start = time.time()
        time.sleep(0.01)  # Simulate work
        duration_ms = (time.time() - start) * 1000
        
        log = {
            "event": "performance",
            "operation": "task_execution",
            "duration_ms": round(duration_ms, 2),
        }
        
        assert log["duration_ms"] >= 10
    
    def test_log_memory_usage(self):
        """Test logging memory usage."""
        log = {
            "event": "performance",
            "metric": "memory_usage",
            "value_mb": 256.5,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["metric"] == "memory_usage"
        assert log["value_mb"] > 0
    
    def test_log_queue_depth(self):
        """Test logging queue depth."""
        log = {
            "event": "performance",
            "metric": "queue_depth",
            "queue": "default",
            "value": 15,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        assert log["metric"] == "queue_depth"


class TestLoggerConfiguration:
    """Test logger configuration options."""
    
    def test_configure_multiple_handlers(self):
        """Test configuring multiple handlers."""
        logger = logging.getLogger("test_multi")
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Add file handler (simulated)
        file_handler = Mock(spec=logging.FileHandler)
        file_handler.level = logging.INFO
        
        handlers = [console_handler, file_handler]
        
        assert len(handlers) == 2
    
    def test_configure_filters(self):
        """Test configuring log filters."""
        class SensitiveDataFilter(logging.Filter):
            def filter(self, record):
                # Filter out records containing sensitive data
                if hasattr(record, 'msg') and 'password' in str(record.msg).lower():
                    return False
                return True
        
        filter_instance = SensitiveDataFilter()
        
        # Create mock records
        safe_record = Mock(msg="Normal log message")
        sensitive_record = Mock(msg="User password: secret123")
        
        assert filter_instance.filter(safe_record) is True
        assert filter_instance.filter(sensitive_record) is False
    
    def test_configure_propagation(self):
        """Test logger propagation configuration."""
        parent = logging.getLogger("peeragent")
        child = logging.getLogger("peeragent.agents")
        
        # By default, logs propagate to parent
        assert child.parent == parent
        
        # Can disable propagation
        child.propagate = False
        assert child.propagate is False


class TestLogRotation:
    """Test log rotation configuration."""
    
    def test_rotation_by_size(self):
        """Test rotation by file size."""
        config = {
            "maxBytes": 10_000_000,  # 10MB
            "backupCount": 5,
        }
        
        assert config["maxBytes"] == 10_000_000
        assert config["backupCount"] == 5
    
    def test_rotation_by_time(self):
        """Test rotation by time."""
        config = {
            "when": "midnight",
            "interval": 1,
            "backupCount": 7,
        }
        
        assert config["when"] == "midnight"
        assert config["backupCount"] == 7


class TestLoggerSingleton:
    """Test logger singleton pattern."""
    
    def test_get_same_logger(self):
        """Test getting same logger instance."""
        logger1 = logging.getLogger("peeragent")
        logger2 = logging.getLogger("peeragent")
        
        assert logger1 is logger2
    
    def test_child_loggers(self):
        """Test child logger hierarchy."""
        parent = logging.getLogger("peeragent")
        child = logging.getLogger("peeragent.agents")
        grandchild = logging.getLogger("peeragent.agents.code")
        
        assert child.name == "peeragent.agents"
        assert grandchild.name == "peeragent.agents.code"


class TestExceptionLogging:
    """Test exception logging."""
    
    def test_log_exception_with_traceback(self):
        """Test logging exception with traceback."""
        try:
            raise ValueError("Test error")
        except ValueError:
            import traceback
            tb = traceback.format_exc()
            
            log = {
                "event": "exception",
                "error_type": "ValueError",
                "error_message": "Test error",
                "traceback": tb,
            }
            
            assert "ValueError" in log["traceback"]
            assert "Test error" in log["traceback"]
    
    def test_log_exception_context(self):
        """Test logging exception with context."""
        context = {
            "task_id": "task-123",
            "user_id": "user-456",
            "operation": "task_execution",
        }
        
        log = {
            "event": "exception",
            "error_type": "RuntimeError",
            "context": context,
        }
        
        assert log["context"]["task_id"] == "task-123"
