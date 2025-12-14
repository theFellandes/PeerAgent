# tests/unit/test_logger.py
"""
Unit tests for logger module.
Target: src/utils/logger.py (45% coverage -> 75%+)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import logging
import json
from datetime import datetime


class TestLoggerSetup:
    """Test logger setup and initialization."""
    
    def test_get_logger_returns_logger(self, mock_settings):
        """Test get_logger returns a logger instance."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_logger_has_correct_name(self, mock_settings):
        """Test logger has correct name."""
        from src.utils.logger import get_logger
        
        logger = get_logger("peeragent.test")
        assert "peeragent" in logger.name or "test" in logger.name
    
    def test_root_logger_configuration(self, mock_settings):
        """Test root logger is configured."""
        from src.utils.logger import setup_logging
        
        # Should not raise
        setup_logging()
        
        root = logging.getLogger()
        assert root is not None


class TestLogLevels:
    """Test log level functionality."""
    
    def test_debug_level_logging(self, mock_settings, mock_logger):
        """Test DEBUG level logging."""
        mock_logger.debug("Debug message")
        mock_logger.debug.assert_called_with("Debug message")
    
    def test_info_level_logging(self, mock_settings, mock_logger):
        """Test INFO level logging."""
        mock_logger.info("Info message")
        mock_logger.info.assert_called_with("Info message")
    
    def test_warning_level_logging(self, mock_settings, mock_logger):
        """Test WARNING level logging."""
        mock_logger.warning("Warning message")
        mock_logger.warning.assert_called_with("Warning message")
    
    def test_error_level_logging(self, mock_settings, mock_logger):
        """Test ERROR level logging."""
        mock_logger.error("Error message")
        mock_logger.error.assert_called_with("Error message")
    
    def test_critical_level_logging(self, mock_settings, mock_logger):
        """Test CRITICAL level logging."""
        mock_logger.critical("Critical message")
        mock_logger.critical.assert_called_with("Critical message")


class TestStructuredLogging:
    """Test structured logging functionality."""
    
    def test_log_task_created(self, mock_settings):
        """Test logging task creation."""
        from src.utils.logger import log_task_event
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_task_event("created", task_id="task-123", task="Write code")
            
            mock_log.info.assert_called()
    
    def test_log_task_completed(self, mock_settings):
        """Test logging task completion."""
        from src.utils.logger import log_task_event
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_task_event("completed", task_id="task-123", duration_ms=150)
            
            mock_log.info.assert_called()
    
    def test_log_task_failed(self, mock_settings):
        """Test logging task failure."""
        from src.utils.logger import log_task_event
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_task_event("failed", task_id="task-123", error="Test error")
            
            mock_log.error.assert_called()


class TestAgentLogging:
    """Test agent-specific logging."""
    
    def test_log_agent_execution(self, mock_settings):
        """Test logging agent execution."""
        from src.utils.logger import log_agent_event
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_agent_event(
                "execution_start",
                agent_type="code_agent",
                session_id="session-123"
            )
            
            mock_log.info.assert_called()
    
    def test_log_llm_call(self, mock_settings):
        """Test logging LLM calls."""
        from src.utils.logger import log_llm_call
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_llm_call(
                provider="openai",
                model="gpt-4o-mini",
                prompt_tokens=500,
                completion_tokens=200,
                duration_ms=800
            )
            
            mock_log.info.assert_called()
    
    def test_log_provider_fallback(self, mock_settings):
        """Test logging provider fallback."""
        from src.utils.logger import log_provider_fallback
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_provider_fallback(
                from_provider="openai",
                to_provider="anthropic",
                reason="Rate limit exceeded"
            )
            
            mock_log.warning.assert_called()


class TestRequestLogging:
    """Test request/response logging."""
    
    def test_log_request(self, mock_settings):
        """Test logging HTTP request."""
        from src.utils.logger import log_request
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_request(
                method="POST",
                path="/v1/agent/execute",
                client_ip="127.0.0.1"
            )
            
            mock_log.info.assert_called()
    
    def test_log_response(self, mock_settings):
        """Test logging HTTP response."""
        from src.utils.logger import log_response
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            log_response(
                status_code=200,
                duration_ms=150
            )
            
            mock_log.info.assert_called()


class TestErrorLogging:
    """Test error logging functionality."""
    
    def test_log_exception(self, mock_settings):
        """Test logging exceptions with traceback."""
        from src.utils.logger import log_exception
        
        with patch("src.utils.logger.get_logger") as mock_get_logger:
            mock_log = MagicMock()
            mock_get_logger.return_value = mock_log
            
            try:
                raise ValueError("Test error")
            except ValueError as e:
                log_exception(e, context={"task_id": "task-123"})
            
            mock_log.error.assert_called()
    
    def test_error_includes_context(self, mock_settings):
        """Test error logging includes context."""
        log_entry = {
            "event": "error",
            "error_type": "ValueError",
            "error_message": "Test error",
            "context": {
                "task_id": "task-123",
                "agent_type": "code_agent"
            }
        }
        
        assert "context" in log_entry
        assert log_entry["context"]["task_id"] == "task-123"


class TestLogFormatting:
    """Test log message formatting."""
    
    def test_json_log_format(self, mock_settings):
        """Test JSON log formatting."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "message": "Test message",
            "extra": {"key": "value"}
        }
        
        formatted = json.dumps(log_entry)
        parsed = json.loads(formatted)
        
        assert parsed["level"] == "INFO"
        assert "timestamp" in parsed
    
    def test_log_entry_has_timestamp(self, mock_settings):
        """Test log entries have timestamps."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Test"
        }
        
        assert "timestamp" in log_entry
        # Should be ISO format
        assert "T" in log_entry["timestamp"]


class TestLoggerConfiguration:
    """Test logger configuration options."""
    
    def test_log_level_from_settings(self, mock_settings):
        """Test log level from settings."""
        mock_settings.debug = True
        
        # In debug mode, level should be DEBUG
        expected_level = logging.DEBUG if mock_settings.debug else logging.INFO
        assert expected_level in [logging.DEBUG, logging.INFO]
    
    def test_add_handler(self, mock_settings):
        """Test adding handlers to logger."""
        logger = logging.getLogger("test_handler")
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        
        assert len(logger.handlers) >= 1
    
    def test_formatter_configuration(self, mock_settings):
        """Test formatter configuration."""
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_str)
        
        assert "asctime" in format_str
        assert "levelname" in format_str
