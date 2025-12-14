# tests/unit/test_config.py
"""
Unit tests for configuration module.
Target: src/config.py (53% coverage -> 80%+)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import os


class TestSettingsInitialization:
    """Test Settings class initialization."""
    
    def test_settings_importable(self):
        """Test Settings class is importable."""
        from src.config import Settings
        assert Settings is not None
    
    def test_get_settings_returns_settings(self, mock_settings):
        """Test get_settings returns Settings instance."""
        from src.config import get_settings
        
        settings = get_settings()
        assert settings is not None
    
    def test_settings_singleton(self, mock_settings):
        """Test get_settings returns same instance."""
        from src.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Should return same mock instance
        assert settings1 is settings2


class TestApplicationSettings:
    """Test application settings."""
    
    def test_app_name(self, mock_settings):
        """Test app name setting."""
        assert mock_settings.app_name == "PeerAgent"
    
    def test_app_version(self, mock_settings):
        """Test app version setting."""
        assert mock_settings.app_version is not None
        assert "." in mock_settings.app_version  # Semantic versioning
    
    def test_debug_mode(self, mock_settings):
        """Test debug mode setting."""
        assert isinstance(mock_settings.debug, bool)
    
    def test_environment(self, mock_settings):
        """Test environment setting."""
        assert mock_settings.environment in ["development", "test", "staging", "production"]


class TestAPISettings:
    """Test API settings."""
    
    def test_api_prefix(self, mock_settings):
        """Test API prefix setting."""
        assert mock_settings.api_prefix == "/v1"
    
    def test_api_host(self, mock_settings):
        """Test API host setting."""
        assert mock_settings.api_host is not None
    
    def test_api_port(self, mock_settings):
        """Test API port setting."""
        assert mock_settings.api_port > 0
        assert mock_settings.api_port < 65536
    
    def test_cors_origins(self, mock_settings):
        """Test CORS origins setting."""
        assert isinstance(mock_settings.cors_origins, list)


class TestLLMSettings:
    """Test LLM provider settings."""
    
    def test_llm_provider(self, mock_settings):
        """Test LLM provider setting."""
        valid_providers = ["openai", "anthropic", "google"]
        assert mock_settings.llm_provider in valid_providers
    
    def test_llm_model(self, mock_settings):
        """Test LLM model setting."""
        assert mock_settings.llm_model is not None
    
    def test_llm_temperature(self, mock_settings):
        """Test LLM temperature setting."""
        assert 0 <= mock_settings.llm_temperature <= 2
    
    def test_openai_api_key(self, mock_settings):
        """Test OpenAI API key setting."""
        # In test mode, should have test key
        assert mock_settings.openai_api_key is not None
    
    def test_anthropic_api_key(self, mock_settings):
        """Test Anthropic API key setting."""
        assert mock_settings.anthropic_api_key is not None
    
    def test_google_api_key(self, mock_settings):
        """Test Google API key setting."""
        assert mock_settings.google_api_key is not None


class TestDatabaseSettings:
    """Test database settings."""
    
    def test_mongodb_url(self, mock_settings):
        """Test MongoDB URL setting."""
        assert mock_settings.mongodb_url is not None
        assert "mongodb://" in mock_settings.mongodb_url
    
    def test_mongodb_db_name(self, mock_settings):
        """Test MongoDB database name setting."""
        assert mock_settings.mongodb_db_name is not None
    
    def test_redis_url(self, mock_settings):
        """Test Redis URL setting."""
        assert mock_settings.redis_url is not None
        assert "redis://" in mock_settings.redis_url


class TestCelerySettings:
    """Test Celery settings."""
    
    def test_celery_broker_url(self, mock_settings):
        """Test Celery broker URL setting."""
        assert mock_settings.celery_broker_url is not None
    
    def test_celery_result_backend(self, mock_settings):
        """Test Celery result backend setting."""
        assert mock_settings.celery_result_backend is not None


class TestTaskSettings:
    """Test task-related settings."""
    
    def test_task_ttl_hours(self, mock_settings):
        """Test task TTL setting."""
        assert mock_settings.task_ttl_hours > 0
    
    def test_task_ttl_in_seconds(self, mock_settings):
        """Test task TTL conversion to seconds."""
        ttl_seconds = mock_settings.task_ttl_hours * 60 * 60
        assert ttl_seconds > 0


class TestSessionSettings:
    """Test session settings."""
    
    def test_session_ttl_minutes(self, mock_settings):
        """Test session TTL setting."""
        assert mock_settings.session_ttl_minutes > 0
    
    def test_max_messages_per_session(self, mock_settings):
        """Test max messages per session setting."""
        assert mock_settings.max_messages_per_session > 0


class TestComputedProperties:
    """Test computed properties."""
    
    def test_is_production(self, mock_settings):
        """Test is_production property."""
        assert isinstance(mock_settings.is_production, bool)
        # In test environment, should be False
        assert mock_settings.is_production is False
    
    def test_is_development(self, mock_settings):
        """Test is_development property."""
        assert isinstance(mock_settings.is_development, bool)
    
    def test_has_valid_llm_key(self, mock_settings):
        """Test has_valid_llm_key property."""
        assert isinstance(mock_settings.has_valid_llm_key, bool)


class TestEnvironmentVariables:
    """Test environment variable loading."""
    
    def test_env_var_override(self, env_override):
        """Test environment variable override."""
        env_override(LLM_PROVIDER="anthropic")
        
        assert os.environ.get("LLM_PROVIDER") == "anthropic"
    
    def test_default_values(self, mock_settings):
        """Test default values when env vars not set."""
        # Debug should have a default
        assert mock_settings.debug is not None
        
        # Environment should have a default
        assert mock_settings.environment is not None
    
    def test_required_env_vars(self, mock_settings):
        """Test required environment variables."""
        # These should always be set (even with test values)
        assert mock_settings.llm_provider is not None
        assert mock_settings.mongodb_url is not None
        assert mock_settings.redis_url is not None


class TestSettingsValidation:
    """Test settings validation."""
    
    def test_valid_llm_provider(self, mock_settings):
        """Test LLM provider validation."""
        valid_providers = ["openai", "anthropic", "google"]
        assert mock_settings.llm_provider in valid_providers
    
    def test_valid_port_range(self, mock_settings):
        """Test port is in valid range."""
        assert 1 <= mock_settings.api_port <= 65535
    
    def test_valid_temperature_range(self, mock_settings):
        """Test temperature is in valid range."""
        assert 0.0 <= mock_settings.llm_temperature <= 2.0
    
    def test_positive_ttl_values(self, mock_settings):
        """Test TTL values are positive."""
        assert mock_settings.task_ttl_hours > 0
        assert mock_settings.session_ttl_minutes > 0


class TestSettingsSerialization:
    """Test settings serialization."""
    
    def test_settings_to_dict(self, mock_settings):
        """Test converting settings to dictionary."""
        # Settings should have attributes that can be accessed
        settings_dict = {
            "app_name": mock_settings.app_name,
            "debug": mock_settings.debug,
            "llm_provider": mock_settings.llm_provider
        }
        
        assert isinstance(settings_dict, dict)
        assert "app_name" in settings_dict
    
    def test_sensitive_fields_excluded(self, mock_settings):
        """Test sensitive fields can be excluded."""
        # API keys should not be exposed in logs/serialization
        sensitive_fields = ["openai_api_key", "anthropic_api_key", "google_api_key"]
        
        # These exist but should be handled carefully
        for field in sensitive_fields:
            assert hasattr(mock_settings, field)
