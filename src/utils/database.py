# Database connection utilities
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis
from redis.asyncio import Redis as AsyncRedis
from functools import lru_cache

from src.config import get_settings


# MongoDB connections
_mongo_client: Optional[AsyncIOMotorClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create async MongoDB client."""
    global _mongo_client
    if _mongo_client is None:
        settings = get_settings()
        _mongo_client = AsyncIOMotorClient(settings.mongodb_url)
    return _mongo_client


async def get_mongo_db():
    """Get the MongoDB database instance."""
    settings = get_settings()
    client = await get_mongo_client()
    return client[settings.mongodb_db_name]


async def close_mongo_connection():
    """Close MongoDB connection."""
    global _mongo_client
    if _mongo_client is not None:
        _mongo_client.close()
        _mongo_client = None


# Redis connections
_redis_client: Optional[Redis] = None
_async_redis_client: Optional[AsyncRedis] = None


def get_redis_client() -> Redis:
    """Get synchronous Redis client."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def get_async_redis_client() -> AsyncRedis:
    """Get async Redis client."""
    global _async_redis_client
    if _async_redis_client is None:
        settings = get_settings()
        _async_redis_client = AsyncRedis.from_url(settings.redis_url, decode_responses=True)
    return _async_redis_client


async def close_redis_connection():
    """Close Redis connections."""
    global _redis_client, _async_redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
    if _async_redis_client is not None:
        await _async_redis_client.close()
        _async_redis_client = None
