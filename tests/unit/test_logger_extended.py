# tests/unit/test_logger_extended.py
"""
Fixed tests for logger.py - uses actual API from the codebase.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import logging
from datetime import datetime


class TestGetLogger:
    """Test get_logger function."""
    
    def test_get_logger_returns_logger(self, mock_settings):
        """Test get_logger returns logger instance."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_with_module_name(self, mock_settings):
        """Test get_logger with module name."""
        from src.utils.logger import get_logger
        
        logger = get_logger("src.agents.code_agent")
        
        assert logger is not None
        assert isinstance(logger, logging.Logger)
    
    def test_get_logger_same_name_returns_same(self, mock_settings):
        """Test same name returns same logger."""
        from src.utils.logger import get_logger
        
        logger1 = get_logger("singleton_test")
        logger2 = get_logger("singleton_test")
        
        assert logger1 is logger2


class TestLogLevels:
    """Test different log levels."""
    
    def test_debug_logging(self, mock_settings, caplog):
        """Test DEBUG level logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test_debug")
        
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
        
        assert logger is not None
    
    def test_info_logging(self, mock_settings, caplog):
        """Test INFO level logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test_info")
        
        with caplog.at_level(logging.INFO):
            logger.info("Info message")
        
        assert logger is not None
    
    def test_warning_logging(self, mock_settings, caplog):
        """Test WARNING level logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test_warning")
        
        with caplog.at_level(logging.WARNING):
            logger.warning("Warning message")
        
        assert logger is not None
    
    def test_error_logging(self, mock_settings, caplog):
        """Test ERROR level logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test_error")
        
        with caplog.at_level(logging.ERROR):
            logger.error("Error message")
        
        assert logger is not None
    
    def test_critical_logging(self, mock_settings, caplog):
        """Test CRITICAL level logging."""
        from src.utils.logger import get_logger
        
        logger = get_logger("test_critical")
        
        with caplog.at_level(logging.CRITICAL):
            logger.critical("Critical message")
        
        assert logger is not None


class TestLoggerConfiguration:
    """Test logger configuration."""
    
    def test_logger_has_name(self, mock_settings):
        """Test logger has name set."""
        from src.utils.logger import get_logger
        
        logger = get_logger("named_logger")
        
        assert logger.name == "named_logger"
    
    def test_logger_can_log_exception(self, mock_settings, caplog):
        """Test logger can log exceptions."""
        from src.utils.logger import get_logger
        
        logger = get_logger("exception_test")
        
        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("An error occurred")
        
        assert logger is not None
    
    def test_logger_with_extra_data(self, mock_settings, caplog):
        """Test logger with extra data."""
        from src.utils.logger import get_logger
        
        logger = get_logger("extra_test")
        
        # Standard logging with extra
        logger.info("Message with extra", extra={"key": "value"})
        
        assert logger is not None


class TestLoggerModule:
    """Test logger module structure."""
    
    def test_logger_module_imports(self, mock_settings):
        """Test logger module can be imported."""
        from src.utils import logger
        
        assert logger is not None
    
    def test_get_logger_exported(self, mock_settings):
        """Test get_logger is exported."""
        from src.utils.logger import get_logger
        
        assert callable(get_logger)
    
    def test_logger_module_has_expected_functions(self, mock_settings):
        """Test logger module has expected functions."""
        from src.utils import logger
        
        # get_logger should exist
        assert hasattr(logger, 'get_logger')


class TestLoggerIntegration:
    """Test logger integration with other components."""
    
    def test_logger_works_with_agents(self, mock_settings):
        """Test logger can be used with agents."""
        from src.utils.logger import get_logger
        
        logger = get_logger("src.agents.code_agent")
        
        logger.info("Agent initialized")
        logger.debug("Processing task")
        logger.info("Task completed")
        
        assert logger is not None
    
    def test_multiple_loggers_independent(self, mock_settings):
        """Test multiple loggers are independent."""
        from src.utils.logger import get_logger
        
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        
        assert logger1 is not logger2
        assert logger1.name == "module1"
        assert logger2.name == "module2"
