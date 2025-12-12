# Logging utilities with MongoDB integration
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
from functools import wraps
from pydantic import BaseModel

from src.config import get_settings


# Standard Python logger
def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if get_settings().debug else logging.INFO)
    return logger


class AgentLogEntry(BaseModel):
    """Schema for agent log entries in MongoDB."""
    timestamp: datetime
    agent_type: str
    session_id: Optional[str]
    task_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    error: Optional[str]
    duration_ms: float
    llm_model: str
    token_usage: Optional[Dict[str, int]]


class MongoDBLogger:
    """Logger that writes structured logs to MongoDB."""
    
    def __init__(self, collection_name: str = "agent_logs"):
        self.collection_name = collection_name
        self._db = None
        self.logger = get_logger(__name__)
    
    async def _get_collection(self):
        """Get the MongoDB collection lazily."""
        if self._db is None:
            from src.utils.database import get_mongo_db
            self._db = await get_mongo_db()
        return self._db[self.collection_name]
    
    async def log(
        self,
        agent_type: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        session_id: Optional[str] = None,
        task_id: Optional[str] = None,
        duration_ms: float = 0.0,
        llm_model: str = "",
        token_usage: Optional[Dict[str, int]] = None
    ) -> str:
        """
        Log an agent interaction to MongoDB.
        
        Returns the inserted document ID.
        """
        entry = AgentLogEntry(
            timestamp=datetime.utcnow(),
            agent_type=agent_type,
            session_id=session_id,
            task_id=task_id,
            input_data=input_data,
            output_data=output_data,
            error=error,
            duration_ms=duration_ms,
            llm_model=llm_model,
            token_usage=token_usage
        )
        
        try:
            collection = await self._get_collection()
            result = await collection.insert_one(entry.model_dump())
            self.logger.debug(f"Logged agent interaction: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            self.logger.error(f"Failed to log to MongoDB: {e}")
            # Fallback to stdout
            self.logger.info(f"Agent Log: {entry.model_dump_json()}")
            return ""
    
    async def get_logs(
        self,
        agent_type: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """Retrieve logs with optional filtering."""
        try:
            collection = await self._get_collection()
            query = {}
            if agent_type:
                query["agent_type"] = agent_type
            if session_id:
                query["session_id"] = session_id
            
            cursor = collection.find(query).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            self.logger.error(f"Failed to retrieve logs: {e}")
            return []


def log_agent_call(agent_type: str):
    """
    Decorator to automatically log agent calls to MongoDB.
    
    Usage:
        @log_agent_call("code_agent")
        async def generate_code(self, task: str) -> CodeOutput:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            start_time = datetime.utcnow()
            logger = MongoDBLogger()
            
            input_data = {
                "args": [str(a) for a in args],
                "kwargs": {k: str(v) for k, v in kwargs.items()}
            }
            
            try:
                result = await func(self, *args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                output_data = None
                if hasattr(result, 'model_dump'):
                    output_data = result.model_dump()
                elif isinstance(result, dict):
                    output_data = result
                
                await logger.log(
                    agent_type=agent_type,
                    input_data=input_data,
                    output_data=output_data,
                    duration_ms=duration,
                    session_id=kwargs.get('session_id'),
                    task_id=kwargs.get('task_id'),
                    llm_model=getattr(self, 'model_name', 'unknown')
                )
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000
                await logger.log(
                    agent_type=agent_type,
                    input_data=input_data,
                    error=str(e),
                    duration_ms=duration,
                    session_id=kwargs.get('session_id'),
                    task_id=kwargs.get('task_id'),
                    llm_model=getattr(self, 'model_name', 'unknown')
                )
                raise
        return wrapper
    return decorator
