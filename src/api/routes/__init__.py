# PeerAgent API Routes
"""
FastAPI router definitions.
"""

from src.api.routes.agent import router as agent_router
from src.api.routes.websocket import router as websocket_router

__all__ = [
    "agent_router",
    "websocket_router",
]
