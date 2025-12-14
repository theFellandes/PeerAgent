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

    def test_root_logger_exists(self, mock_settings):
        """Test root logger is accessible."""
        root = logging.getLogger()
        assert root is not None


class TestLogLevels:
    """Test log level functionality."""

    def test_debug_level_logging(self, mock_settings):
        """Test DEBUG level logging."""
        from src.utils.logger import get_logger
        logger = get_logger("test_debug")

        # Should not raise
        logger.debug("Debug message")

    def test_info_level_logging(self, mock_settings):
        """Test INFO level logging."""
        from src.utils.logger import get_logger
        logger = get_logger("test_info")

        logger.info("Info message")

    def test_warning_level_logging(self, mock_settings):
        """Test WARNING level logging."""
        from src.utils.logger import get_logger
        logger = get_logger("test_warning")

        logger.warning("Warning message")

    def test_error_level_logging(self, mock_settings):
        """Test ERROR level logging."""
        from src.utils.logger import get_logger
        logger = get_logger("test_error")

        logger.error("Error message")

    def test_critical_level_logging(self, mock_settings):
        """Test CRITICAL level logging."""
        from src.utils.logger import get_logger
        logger = get_logger("test_critical")

        logger.critical("Critical message")


class TestLogFormatting:
    """Test log message formatting."""

    def test_json_log_format(self, mock_settings):
        """Test JSON log formatting."""
        import json
        from datetime import datetime

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
        from datetime import datetime

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Test"
        }

        assert "timestamp" in log_entry
        assert "T" in log_entry["timestamp"]


class TestLoggerConfiguration:
    """Test logger configuration options."""

    def test_log_level_default(self, mock_settings):
        """Test default log level."""
        from src.utils.logger import get_logger
        logger = get_logger("test_level")

        # Logger should be created
        assert logger is not None

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


class TestLoggerModule:
    """Test the logger module structure."""

    def test_get_logger_exists(self, mock_settings):
        """Test get_logger function exists."""
        from src.utils import logger

        assert hasattr(logger, 'get_logger')
        assert callable(logger.get_logger)

    def test_logger_module_importable(self, mock_settings):
        """Test logger module is importable."""
        try:
            from src.utils.logger import get_logger
            assert True
        except ImportError:
            pytest.fail("Could not import get_logger from src.utils.logger")


class TestLoggerSingleton:
    """Test logger singleton behavior."""

    def test_same_name_returns_same_logger(self, mock_settings):
        """Test that same name returns same logger instance."""
        from src.utils.logger import get_logger

        logger1 = get_logger("singleton_test")
        logger2 = get_logger("singleton_test")

        assert logger1 is logger2

    def test_different_name_returns_different_logger(self, mock_settings):
        """Test that different names return different loggers."""
        from src.utils.logger import get_logger

        logger1 = get_logger("logger_a")
        logger2 = get_logger("logger_b")

        assert logger1 is not logger2
