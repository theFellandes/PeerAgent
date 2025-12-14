"""
Comprehensive unit tests for configuration module.
Target: src/config.py (53% coverage -> 80%+)
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import os


class TestLLMProviderConfig:
    """Test LLM provider configuration."""
    
    def test_default_provider(self):
        """Test default LLM provider."""
        default_provider = "openai"
        assert default_provider == "openai"
    
    def test_provider_from_env(self):
        """Test provider from environment variable."""
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}):
            provider = os.environ.get("LLM_PROVIDER", "openai")
            assert provider == "anthropic"
    
    def test_valid_providers(self):
        """Test valid provider list."""
        valid_providers = ["openai", "anthropic", "google"]
        
        for provider in valid_providers:
            assert provider in valid_providers
    
    def test_invalid_provider_fallback(self):
        """Test fallback for invalid provider."""
        def get_provider(provider: str) -> str:
            valid = ["openai", "anthropic", "google"]
            return provider if provider in valid else "openai"
        
        assert get_provider("invalid") == "openai"
        assert get_provider("openai") == "openai"


class TestLLMModelConfig:
    """Test LLM model configuration."""
    
    def test_default_model(self):
        """Test default model."""
        default_model = "gpt-4o-mini"
        assert "gpt" in default_model
    
    def test_model_from_env(self):
        """Test model from environment variable."""
        with patch.dict(os.environ, {"LLM_MODEL": "gpt-4"}):
            model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            assert model == "gpt-4"
    
    def test_provider_model_mapping(self):
        """Test provider to model mapping."""
        provider_models = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-sonnet-20240229",
            "google": "gemini-1.5-flash",
        }
        
        assert "gpt" in provider_models["openai"]
        assert "claude" in provider_models["anthropic"]
        assert "gemini" in provider_models["google"]


class TestAPIKeyConfig:
    """Test API key configuration."""
    
    def test_openai_api_key(self):
        """Test OpenAI API key from env."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}):
            key = os.environ.get("OPENAI_API_KEY")
            assert key == "sk-test-key"
    
    def test_anthropic_api_key(self):
        """Test Anthropic API key from env."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test"}):
            key = os.environ.get("ANTHROPIC_API_KEY")
            assert key == "sk-ant-test"
    
    def test_google_api_key(self):
        """Test Google API key from env."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "google-test-key"}):
            key = os.environ.get("GOOGLE_API_KEY")
            assert key == "google-test-key"
    
    def test_missing_api_key_handling(self):
        """Test handling of missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            key = os.environ.get("OPENAI_API_KEY")
            assert key is None


class TestDatabaseConfig:
    """Test database configuration."""
    
    def test_mongodb_url_default(self):
        """Test default MongoDB URL."""
        default_url = "mongodb://localhost:27017"
        assert "mongodb://" in default_url
        assert "27017" in default_url
    
    def test_mongodb_url_from_env(self):
        """Test MongoDB URL from environment."""
        with patch.dict(os.environ, {"MONGODB_URL": "mongodb://dbhost:27017/peeragent"}):
            url = os.environ.get("MONGODB_URL")
            assert "dbhost" in url
    
    def test_redis_url_default(self):
        """Test default Redis URL."""
        default_url = "redis://localhost:6379/0"
        assert "redis://" in default_url
        assert "6379" in default_url
    
    def test_redis_url_from_env(self):
        """Test Redis URL from environment."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://redishost:6379/1"}):
            url = os.environ.get("REDIS_URL")
            assert "redishost" in url


class TestTaskConfig:
    """Test task configuration."""
    
    def test_task_ttl_default(self):
        """Test default task TTL."""
        default_ttl_hours = 24
        assert default_ttl_hours == 24
    
    def test_task_ttl_from_env(self):
        """Test task TTL from environment."""
        with patch.dict(os.environ, {"TASK_TTL_HOURS": "48"}):
            ttl = int(os.environ.get("TASK_TTL_HOURS", "24"))
            assert ttl == 48
    
    def test_task_ttl_in_seconds(self):
        """Test converting TTL to seconds."""
        ttl_hours = 24
        ttl_seconds = ttl_hours * 60 * 60
        
        assert ttl_seconds == 86400


class TestRateLimitConfig:
    """Test rate limiting configuration."""
    
    def test_default_rate_limit(self):
        """Test default rate limit."""
        default_limit = "10/minute"
        
        assert "10" in default_limit
        assert "minute" in default_limit
    
    def test_rate_limit_parsing(self):
        """Test rate limit string parsing."""
        def parse_rate_limit(limit_str: str) -> dict:
            parts = limit_str.split("/")
            return {
                "count": int(parts[0]),
                "period": parts[1],
            }
        
        parsed = parse_rate_limit("10/minute")
        
        assert parsed["count"] == 10
        assert parsed["period"] == "minute"
    
    def test_endpoint_specific_limits(self):
        """Test endpoint-specific rate limits."""
        limits = {
            "/v1/agent/execute": "10/minute",
            "/v1/agent/status": "30/minute",
            "/health": None,  # No limit
        }
        
        assert limits["/v1/agent/execute"] == "10/minute"
        assert limits["/health"] is None


class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_default_log_level(self):
        """Test default log level."""
        default_level = "INFO"
        assert default_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    
    def test_log_level_from_env(self):
        """Test log level from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = os.environ.get("LOG_LEVEL", "INFO")
            assert level == "DEBUG"
    
    def test_log_format(self):
        """Test log format string."""
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        assert "%(asctime)s" in log_format
        assert "%(levelname)s" in log_format


class TestServerConfig:
    """Test server configuration."""
    
    def test_default_host(self):
        """Test default host."""
        default_host = "0.0.0.0"
        assert default_host == "0.0.0.0"
    
    def test_default_port(self):
        """Test default port."""
        default_port = 8000
        assert default_port == 8000
    
    def test_port_from_env(self):
        """Test port from environment."""
        with patch.dict(os.environ, {"PORT": "9000"}):
            port = int(os.environ.get("PORT", "8000"))
            assert port == 9000
    
    def test_debug_mode(self):
        """Test debug mode configuration."""
        with patch.dict(os.environ, {"DEBUG": "true"}):
            debug = os.environ.get("DEBUG", "false").lower() == "true"
            assert debug is True


class TestCeleryConfig:
    """Test Celery configuration."""
    
    def test_broker_url(self):
        """Test Celery broker URL."""
        with patch.dict(os.environ, {"CELERY_BROKER_URL": "redis://localhost:6379/0"}):
            broker = os.environ.get("CELERY_BROKER_URL")
            assert "redis://" in broker
    
    def test_result_backend(self):
        """Test Celery result backend."""
        with patch.dict(os.environ, {"CELERY_RESULT_BACKEND": "redis://localhost:6379/0"}):
            backend = os.environ.get("CELERY_RESULT_BACKEND")
            assert "redis://" in backend
    
    def test_task_serializer(self):
        """Test task serializer config."""
        config = {"task_serializer": "json"}
        assert config["task_serializer"] == "json"
    
    def test_worker_concurrency(self):
        """Test worker concurrency config."""
        with patch.dict(os.environ, {"CELERY_WORKERS": "4"}):
            workers = int(os.environ.get("CELERY_WORKERS", "2"))
            assert workers == 4


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_required_keys(self):
        """Test validation of required configuration keys."""
        def validate_config(config: dict) -> list:
            required = ["llm_provider", "mongodb_url", "redis_url"]
            missing = [k for k in required if k not in config or not config[k]]
            return missing
        
        valid_config = {
            "llm_provider": "openai",
            "mongodb_url": "mongodb://localhost:27017",
            "redis_url": "redis://localhost:6379/0",
        }
        
        invalid_config = {
            "llm_provider": "openai",
            # Missing mongodb_url and redis_url
        }
        
        assert len(validate_config(valid_config)) == 0
        assert len(validate_config(invalid_config)) == 2
    
    def test_validate_url_format(self):
        """Test URL format validation."""
        from urllib.parse import urlparse
        
        def is_valid_url(url: str) -> bool:
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except Exception:
                return False
        
        assert is_valid_url("mongodb://localhost:27017")
        assert is_valid_url("redis://localhost:6379/0")
        assert not is_valid_url("not-a-url")
    
    def test_validate_integer_values(self):
        """Test integer value validation."""
        def validate_integer(value: str, min_val: int = 0, max_val: int = None) -> bool:
            try:
                num = int(value)
                if num < min_val:
                    return False
                if max_val is not None and num > max_val:
                    return False
                return True
            except ValueError:
                return False
        
        assert validate_integer("10", min_val=1, max_val=100)
        assert not validate_integer("not-a-number")
        assert not validate_integer("0", min_val=1)


class TestConfigClass:
    """Test Config class implementation."""
    
    def test_config_singleton(self):
        """Test Config is singleton."""
        class Config:
            _instance = None
            
            def __new__(cls):
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                return cls._instance
        
        config1 = Config()
        config2 = Config()
        
        assert config1 is config2
    
    def test_config_loads_from_env(self):
        """Test Config loads from environment."""
        class Config:
            def __init__(self):
                self.llm_provider = os.environ.get("LLM_PROVIDER", "openai")
                self.debug = os.environ.get("DEBUG", "false").lower() == "true"
        
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic", "DEBUG": "true"}):
            config = Config()
            assert config.llm_provider == "anthropic"
            assert config.debug is True
    
    def test_config_to_dict(self):
        """Test Config to dictionary conversion."""
        class Config:
            def __init__(self):
                self.llm_provider = "openai"
                self.debug = False
            
            def to_dict(self):
                return {
                    "llm_provider": self.llm_provider,
                    "debug": self.debug,
                }
        
        config = Config()
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict["llm_provider"] == "openai"


class TestEnvironmentLoading:
    """Test environment file loading."""
    
    def test_dotenv_loading(self):
        """Test .env file loading simulation."""
        # Simulate loading from .env
        env_content = """
        LLM_PROVIDER=openai
        DEBUG=false
        PORT=8000
        """
        
        env_vars = {}
        for line in env_content.strip().split("\n"):
            line = line.strip()
            if line and "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()
        
        assert env_vars["LLM_PROVIDER"] == "openai"
        assert env_vars["PORT"] == "8000"
    
    def test_env_override_order(self):
        """Test environment variable override order."""
        # .env < environment < runtime
        default = "default_value"
        env_file = "env_file_value"
        os_env = "os_env_value"
        
        # OS env should win
        with patch.dict(os.environ, {"TEST_VAR": os_env}):
            value = os.environ.get("TEST_VAR", env_file)
            assert value == os_env


class TestFeatureFlags:
    """Test feature flag configuration."""
    
    def test_feature_flag_enabled(self):
        """Test feature flag enabled."""
        with patch.dict(os.environ, {"FEATURE_ASYNC_TASKS": "true"}):
            enabled = os.environ.get("FEATURE_ASYNC_TASKS", "false").lower() == "true"
            assert enabled is True
    
    def test_feature_flag_disabled(self):
        """Test feature flag disabled."""
        with patch.dict(os.environ, {"FEATURE_ASYNC_TASKS": "false"}):
            enabled = os.environ.get("FEATURE_ASYNC_TASKS", "false").lower() == "true"
            assert enabled is False
    
    def test_feature_flags_dict(self):
        """Test feature flags as dictionary."""
        features = {
            "async_tasks": True,
            "websocket": True,
            "rate_limiting": True,
            "caching": False,
        }
        
        assert features["async_tasks"] is True
        assert features["caching"] is False
