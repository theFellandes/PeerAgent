# Database connection utilities with connection pooling
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis, ConnectionPool
from redis.asyncio import Redis as AsyncRedis
from redis.asyncio import ConnectionPool as AsyncConnectionPool

from src.config import get_settings


# MongoDB connections
_mongo_client: Optional[AsyncIOMotorClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create async MongoDB client with connection pooling."""
    global _mongo_client
    if _mongo_client is None:
        settings = get_settings()
        _mongo_client = AsyncIOMotorClient(
            settings.mongodb_url,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            waitQueueTimeoutMS=5000,
        )
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


# Redis connection pools
_redis_pool: Optional[ConnectionPool] = None
_async_redis_pool: Optional[AsyncConnectionPool] = None
_redis_client: Optional[Redis] = None
_async_redis_client: Optional[AsyncRedis] = None


def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        settings = get_settings()
        _redis_pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
    return _redis_pool


def get_redis_client() -> Redis:
    """Get synchronous Redis client with connection pooling."""
    global _redis_client
    if _redis_client is None:
        pool = get_redis_pool()
        _redis_client = Redis(connection_pool=pool)
    return _redis_client


async def get_async_redis_pool() -> AsyncConnectionPool:
    """Get or create async Redis connection pool."""
    global _async_redis_pool
    if _async_redis_pool is None:
        settings = get_settings()
        _async_redis_pool = AsyncConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
    return _async_redis_pool


async def get_async_redis_client() -> AsyncRedis:
    """Get async Redis client with connection pooling."""
    global _async_redis_client
    if _async_redis_client is None:
        pool = await get_async_redis_pool()
        _async_redis_client = AsyncRedis(connection_pool=pool)
    return _async_redis_client


async def close_redis_connection():
    """Close Redis connections and pools."""
    global _redis_client, _async_redis_client, _redis_pool, _async_redis_pool
    
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
    
    if _async_redis_client is not None:
        await _async_redis_client.close()
        _async_redis_client = None
    
    if _redis_pool is not None:
        _redis_pool.disconnect()
        _redis_pool = None
    
    if _async_redis_pool is not None:
        await _async_redis_pool.disconnect()
        _async_redis_pool = None
