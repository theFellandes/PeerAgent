# Redis-backed Task Store
"""
Persistent task storage using Redis instead of in-memory dictionary.
Provides durability, scalability, and multi-instance support.
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import redis
from redis import Redis
from pydantic import BaseModel, Field

from src.config import get_settings
from src.utils.logger import get_logger

logger = get_logger("TaskStore")


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskData(BaseModel):
    """Schema for task data stored in Redis."""
    task_id: str
    status: TaskStatus
    task: str
    session_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    agent_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RedisTaskStore:
    """
    Redis-backed task store for persistent task management.
    
    Features:
    - Persistent storage across restarts
    - TTL-based expiration for old tasks
    - Atomic operations for task updates
    - Support for task listing and filtering
    """
    
    _instance: Optional["RedisTaskStore"] = None
    
    def __new__(cls):
        """Singleton pattern for shared task store."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        settings = get_settings()
        self._redis: Optional[Redis] = None
        self._redis_url = settings.redis_url
        self._prefix = "peeragent:task:"
        self._ttl_hours = 24  # Tasks expire after 24 hours
        self._initialized = True
        logger.info("RedisTaskStore initialized")
    
    @property
    def redis(self) -> Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True
            )
            # Test connection
            try:
                self._redis.ping()
                logger.info("Redis connection established")
            except redis.ConnectionError as e:
                logger.error(f"Redis connection failed: {e}")
                raise
        return self._redis
    
    def _key(self, task_id: str) -> str:
        """Generate Redis key for task."""
        return f"{self._prefix}{task_id}"
    
    def create(self, task_data: TaskData) -> TaskData:
        """
        Create a new task in the store.
        
        Args:
            task_data: TaskData object with task information
            
        Returns:
            The created TaskData
        """
        key = self._key(task_data.task_id)
        data = task_data.model_dump_json()
        
        # Set with TTL
        ttl_seconds = self._ttl_hours * 3600
        self.redis.setex(key, ttl_seconds, data)
        
        # Add to task index for listing
        self.redis.zadd(
            f"{self._prefix}index",
            {task_data.task_id: datetime.utcnow().timestamp()}
        )
        
        logger.debug(f"Created task: {task_data.task_id}")
        return task_data
    
    def get(self, task_id: str) -> Optional[TaskData]:
        """
        Get a task by ID.
        
        Args:
            task_id: The task identifier
            
        Returns:
            TaskData if found, None otherwise
        """
        key = self._key(task_id)
        data = self.redis.get(key)
        
        if data is None:
            return None
        
        return TaskData.model_validate_json(data)
    
    def update(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskData]:
        """
        Update a task with new data.
        
        Args:
            task_id: The task identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated TaskData if found, None otherwise
        """
        task = self.get(task_id)
        if task is None:
            return None
        
        # Apply updates
        task_dict = task.model_dump()
        task_dict.update(updates)
        
        # Validate and save
        updated_task = TaskData(**task_dict)
        key = self._key(task_id)
        
        # Preserve remaining TTL or set new one
        ttl = self.redis.ttl(key)
        if ttl < 0:
            ttl = self._ttl_hours * 3600
        
        self.redis.setex(key, ttl, updated_task.model_dump_json())
        
        logger.debug(f"Updated task: {task_id}")
        return updated_task
    
    def delete(self, task_id: str) -> bool:
        """
        Delete a task from the store.
        
        Args:
            task_id: The task identifier
            
        Returns:
            True if deleted, False if not found
        """
        key = self._key(task_id)
        result = self.redis.delete(key)
        
        # Remove from index
        self.redis.zrem(f"{self._prefix}index", task_id)
        
        if result:
            logger.debug(f"Deleted task: {task_id}")
        
        return result > 0
    
    def exists(self, task_id: str) -> bool:
        """Check if a task exists."""
        return self.redis.exists(self._key(task_id)) > 0
    
    def list_tasks(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[TaskStatus] = None
    ) -> List[TaskData]:
        """
        List tasks with optional filtering.
        
        Args:
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            status: Optional status filter
            
        Returns:
            List of TaskData objects
        """
        # Get task IDs from index (sorted by creation time, newest first)
        task_ids = self.redis.zrevrange(
            f"{self._prefix}index",
            offset,
            offset + limit - 1
        )
        
        tasks = []
        for task_id in task_ids:
            task = self.get(task_id)
            if task is not None:
                if status is None or task.status == status:
                    tasks.append(task)
        
        return tasks
    
    def get_session_tasks(self, session_id: str, limit: int = 50) -> List[TaskData]:
        """
        Get all tasks for a specific session.
        
        Args:
            session_id: The session identifier
            limit: Maximum number of tasks to return
            
        Returns:
            List of TaskData objects for the session
        """
        all_tasks = self.list_tasks(limit=limit * 2)  # Fetch more to filter
        return [t for t in all_tasks if t.session_id == session_id][:limit]
    
    def cleanup_expired(self) -> int:
        """
        Remove expired task IDs from the index.
        
        Returns:
            Number of removed entries
        """
        # Get all task IDs from index
        task_ids = self.redis.zrange(f"{self._prefix}index", 0, -1)
        
        removed = 0
        for task_id in task_ids:
            if not self.exists(task_id):
                self.redis.zrem(f"{self._prefix}index", task_id)
                removed += 1
        
        if removed:
            logger.info(f"Cleaned up {removed} expired task index entries")
        
        return removed
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get task store statistics.
        
        Returns:
            Dictionary with stats
        """
        total = self.redis.zcard(f"{self._prefix}index")
        
        # Count by status
        status_counts = {}
        sample = self.list_tasks(limit=1000)
        for task in sample:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": total,
            "status_counts": status_counts,
            "ttl_hours": self._ttl_hours
        }
    
    def close(self):
        """Close Redis connection."""
        if self._redis is not None:
            self._redis.close()
            self._redis = None
            logger.info("Redis connection closed")


# Fallback in-memory store for when Redis is unavailable
class InMemoryTaskStore:
    """
    Fallback in-memory task store.
    Used when Redis is not available.
    """
    
    _instance: Optional["InMemoryTaskStore"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._store: Dict[str, TaskData] = {}
        self._initialized = True
        logger.warning("Using in-memory task store (Redis unavailable)")
    
    def create(self, task_data: TaskData) -> TaskData:
        self._store[task_data.task_id] = task_data
        return task_data
    
    def get(self, task_id: str) -> Optional[TaskData]:
        return self._store.get(task_id)
    
    def update(self, task_id: str, updates: Dict[str, Any]) -> Optional[TaskData]:
        task = self._store.get(task_id)
        if task is None:
            return None
        
        task_dict = task.model_dump()
        task_dict.update(updates)
        updated = TaskData(**task_dict)
        self._store[task_id] = updated
        return updated
    
    def delete(self, task_id: str) -> bool:
        if task_id in self._store:
            del self._store[task_id]
            return True
        return False
    
    def exists(self, task_id: str) -> bool:
        return task_id in self._store
    
    def list_tasks(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[TaskStatus] = None
    ) -> List[TaskData]:
        tasks = list(self._store.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return tasks[offset:offset + limit]
    
    def get_session_tasks(self, session_id: str, limit: int = 50) -> List[TaskData]:
        return [
            t for t in self._store.values()
            if t.session_id == session_id
        ][:limit]
    
    def cleanup_expired(self) -> int:
        return 0  # No-op for in-memory
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_tasks": len(self._store),
            "status_counts": {},
            "type": "in-memory"
        }
    
    def close(self):
        pass


def get_task_store() -> RedisTaskStore:
    """
    Get the task store instance.
    
    Returns RedisTaskStore if Redis is available,
    falls back to InMemoryTaskStore otherwise.
    """
    try:
        store = RedisTaskStore()
        store.redis.ping()  # Test connection
        return store
    except Exception as e:
        logger.warning(f"Redis unavailable, using in-memory store: {e}")
        return InMemoryTaskStore()
