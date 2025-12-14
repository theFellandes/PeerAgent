# Configuration management for PeerAgent system (Improved)
"""
Centralized configuration with environment variable support.

Features:
- Pydantic settings with validation
- Environment variable loading
- Default values for development
- Type-safe configuration
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables.
    Variable names are case-insensitive.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==========================================================================
    # Application Settings
    # ==========================================================================
    app_name: str = Field(default="PeerAgent", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    
    # ==========================================================================
    # API Settings
    # ==========================================================================
    api_prefix: str = Field(default="/v1", description="API route prefix")
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    
    # Rate Limiting
    rate_limit_execute: str = Field(default="10/minute", description="Rate limit for execute endpoint")
    rate_limit_status: str = Field(default="30/minute", description="Rate limit for status endpoint")
    rate_limit_default: str = Field(default="60/minute", description="Default rate limit")
    
    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    llm_provider: str = Field(
        default="openai",
        description="Primary LLM provider: openai, anthropic, google"
    )
    llm_model: str = Field(
        default="gpt-4o-mini",
        description="LLM model name"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens in LLM response"
    )
    llm_timeout: int = Field(
        default=120,
        description="LLM request timeout in seconds"
    )
    
    # API Keys (with fallback)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic API key (fallback)"
    )
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google API key (fallback)"
    )
    
    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    # MongoDB
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL"
    )
    mongodb_db_name: str = Field(
        default="peeragent",
        description="MongoDB database name"
    )
    mongodb_pool_size: int = Field(
        default=50,
        description="MongoDB connection pool size"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_pool_size: int = Field(
        default=20,
        description="Redis connection pool size"
    )
    
    # ==========================================================================
    # Celery Configuration
    # ==========================================================================
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0",
        description="Celery broker URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0",
        description="Celery result backend URL"
    )
    celery_worker_concurrency: int = Field(
        default=4,
        description="Celery worker concurrency"
    )
    celery_task_timeout: int = Field(
        default=360,
        description="Celery task timeout in seconds"
    )
    
    # ==========================================================================
    # Task Store Configuration
    # ==========================================================================
    task_ttl_hours: int = Field(
        default=24,
        description="Task TTL in hours (after which tasks are cleaned up)"
    )
    
    # ==========================================================================
    # Session/Memory Configuration
    # ==========================================================================
    session_ttl_minutes: int = Field(
        default=60,
        description="Session TTL in minutes"
    )
    max_messages_per_session: int = Field(
        default=50,
        description="Maximum messages to retain per session"
    )
    
    # ==========================================================================
    # Logging Configuration
    # ==========================================================================
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR"
    )
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # ==========================================================================
    # Validators
    # ==========================================================================
    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v):
        valid_providers = ["openai", "anthropic", "google"]
        v = v.lower()
        if v not in valid_providers:
            raise ValueError(f"llm_provider must be one of {valid_providers}")
        return v
    
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production", "test"]
        v = v.lower()
        if v not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v
    
    # ==========================================================================
    # Computed Properties
    # ==========================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def has_valid_llm_key(self) -> bool:
        """Check if at least one LLM API key is configured."""
        return any([
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key
        ])
    
    def get_llm_fallback_order(self) -> List[str]:
        """Get LLM providers in fallback order based on available keys."""
        order = []
        
        # Primary first
        if self.llm_provider == "openai" and self.openai_api_key:
            order.append("openai")
        elif self.llm_provider == "anthropic" and self.anthropic_api_key:
            order.append("anthropic")
        elif self.llm_provider == "google" and self.google_api_key:
            order.append("google")
        
        # Add others as fallbacks
        if "openai" not in order and self.openai_api_key:
            order.append("openai")
        if "google" not in order and self.google_api_key:
            order.append("google")
        if "anthropic" not in order and self.anthropic_api_key:
            order.append("anthropic")
        
        return order


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Settings are loaded once and cached for performance.
    To reload, clear the cache with get_settings.cache_clear()
    """
    return Settings()


def get_env_info() -> dict:
    """Get environment information for debugging."""
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.environment,
        "debug": settings.debug,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "has_openai_key": bool(settings.openai_api_key),
        "has_anthropic_key": bool(settings.anthropic_api_key),
        "has_google_key": bool(settings.google_api_key),
        "mongodb_db": settings.mongodb_db_name,
        "api_prefix": settings.api_prefix
    }
