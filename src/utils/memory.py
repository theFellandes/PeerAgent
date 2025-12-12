# Session Memory Store for LangGraph
"""
Provides session-based memory storage for conversation history.
This allows agents to retain context across multiple interactions.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import asyncio
from src.utils.logger import get_logger

logger = get_logger("MemoryStore")


@dataclass
class SessionMemory:
    """Memory for a single session."""
    session_id: str
    messages: List[BaseMessage] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    
    def add_message(self, message: BaseMessage):
        """Add a message to the session."""
        self.messages.append(message)
        self.last_accessed = datetime.utcnow()
    
    def add_human_message(self, content: str):
        """Add a human message."""
        self.add_message(HumanMessage(content=content))
    
    def add_ai_message(self, content: str):
        """Add an AI message."""
        self.add_message(AIMessage(content=content))
    
    def get_context_window(self, max_messages: int = 10) -> List[BaseMessage]:
        """Get the most recent messages for context."""
        return self.messages[-max_messages:]
    
    def set_context(self, key: str, value: Any):
        """Store contextual information."""
        self.context[key] = value
        self.last_accessed = datetime.utcnow()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Retrieve contextual information."""
        return self.context.get(key, default)


class MemoryStore:
    """
    In-memory store for session-based conversations.
    Supports TTL-based cleanup and context persistence.
    """
    
    _instance: Optional["MemoryStore"] = None
    
    def __new__(cls):
        """Singleton pattern for shared memory."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._sessions: Dict[str, SessionMemory] = {}
        self._ttl_minutes: int = 60  # Sessions expire after 60 minutes
        self._initialized = True
        logger.info("MemoryStore initialized")
    
    def get_session(self, session_id: str) -> SessionMemory:
        """Get or create a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id=session_id)
            logger.info(f"Created new session: {session_id}")
        
        session = self._sessions[session_id]
        session.last_accessed = datetime.utcnow()
        return session
    
    def get_messages(self, session_id: str, max_messages: int = 10) -> List[BaseMessage]:
        """Get recent messages from a session."""
        session = self.get_session(session_id)
        return session.get_context_window(max_messages)
    
    def add_interaction(self, session_id: str, human_message: str, ai_response: str):
        """Record a complete interaction (human + AI response)."""
        session = self.get_session(session_id)
        session.add_human_message(human_message)
        session.add_ai_message(ai_response)
        logger.debug(f"Added interaction to session {session_id}, total: {len(session.messages)}")
    
    def set_context(self, session_id: str, key: str, value: Any):
        """Store context for a session."""
        session = self.get_session(session_id)
        session.set_context(key, value)
    
    def get_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """Get context from a session."""
        session = self.get_session(session_id)
        return session.get_context(key, default)
    
    def clear_session(self, session_id: str):
        """Clear a session's memory."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
    
    def cleanup_expired(self):
        """Remove expired sessions."""
        now = datetime.utcnow()
        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.last_accessed > timedelta(minutes=self._ttl_minutes)
        ]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        return {
            "active_sessions": len(self._sessions),
            "total_messages": sum(len(s.messages) for s in self._sessions.values()),
        }


# Global memory store instance
memory_store = MemoryStore()


def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    return memory_store
