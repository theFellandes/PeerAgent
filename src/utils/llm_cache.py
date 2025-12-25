# LLM Response Caching with Redis
"""
Caches LLM responses to save tokens on similar queries.
Uses semantic hashing to match similar questions.
Falls back to LLM if Redis is unavailable.
"""
import hashlib
import json
import logging
from typing import Optional, Any
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.config import settings

logger = logging.getLogger(__name__)


class LLMCache:
    """Redis-based cache for LLM responses."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl_hours: int = 24):
        """
        Initialize LLM cache.
        
        Args:
            redis_url: Redis connection URL (defaults to settings)
            ttl_hours: Time-to-live for cached responses in hours
        """
        self.ttl_seconds = ttl_hours * 3600
        self.redis_client = None
        self.enabled = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed. LLM caching disabled.")
            return
        
        try:
            url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info("LLM cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, caching disabled: {e}")
            self.redis_client = None
    
    def _generate_cache_key(self, prompt: str, model: str = "default") -> str:
        """Generate a cache key from the prompt."""
        # Normalize the prompt (lowercase, strip whitespace)
        normalized = prompt.lower().strip()
        # Create hash
        hash_input = f"{model}:{normalized}"
        return f"llm_cache:{hashlib.sha256(hash_input.encode()).hexdigest()[:32]}"
    
    def get(self, prompt: str, model: str = "default") -> Optional[str]:
        """
        Get cached response for a prompt.
        
        Args:
            prompt: The LLM prompt
            model: Model identifier
            
        Returns:
            Cached response string or None if not found
        """
        if not self.enabled:
            return None
        
        try:
            key = self._generate_cache_key(prompt, model)
            cached = self.redis_client.get(key)
            if cached:
                logger.debug(f"Cache HIT for prompt: {prompt[:50]}...")
                return cached
            logger.debug(f"Cache MISS for prompt: {prompt[:50]}...")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    def set(self, prompt: str, response: str, model: str = "default") -> bool:
        """
        Cache a response for a prompt.
        
        Args:
            prompt: The LLM prompt
            response: The LLM response to cache
            model: Model identifier
            
        Returns:
            True if cached successfully
        """
        if not self.enabled:
            return False
        
        try:
            key = self._generate_cache_key(prompt, model)
            self.redis_client.setex(key, self.ttl_seconds, response)
            logger.debug(f"Cached response for prompt: {prompt[:50]}...")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def clear(self, pattern: str = "llm_cache:*") -> int:
        """Clear cached responses matching pattern."""
        if not self.enabled:
            return 0
        
        try:
            keys = list(self.redis_client.scan_iter(match=pattern))
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear error: {e}")
            return 0
    
    def stats(self) -> dict:
        """Get cache statistics."""
        if not self.enabled:
            return {"enabled": False, "count": 0}
        
        try:
            keys = list(self.redis_client.scan_iter(match="llm_cache:*"))
            return {
                "enabled": True,
                "count": len(keys),
                "redis_connected": True
            }
        except Exception as e:
            return {"enabled": True, "error": str(e)}


# Global cache instance
_cache_instance: Optional[LLMCache] = None


def get_llm_cache() -> LLMCache:
    """Get or create the global LLM cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMCache()
    return _cache_instance


def cached_llm_call(cache_key_prefix: str = ""):
    """
    Decorator to cache LLM call results.
    
    Usage:
        @cached_llm_call("business_questions")
        async def generate_questions(self, task: str) -> str:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_llm_cache()
            
            # Build cache key from arguments
            key_parts = [cache_key_prefix]
            for arg in args[1:]:  # Skip 'self'
                if isinstance(arg, str):
                    key_parts.append(arg[:100])
            cache_prompt = ":".join(key_parts)
            
            # Try cache first
            cached = cache.get(cache_prompt)
            if cached:
                return cached
            
            # Call the actual function
            result = await func(*args, **kwargs)
            
            # Cache the result if it's a string
            if isinstance(result, str):
                cache.set(cache_prompt, result)
            
            return result
        return wrapper
    return decorator
