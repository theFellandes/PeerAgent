# FastAPI Application - Main Entry Point (Improved)
"""
PeerAgent API Server

Features:
- FastAPI with async support
- WebSocket for real-time communication
- Redis-backed task storage
- Rate limiting
- Comprehensive health checks
- CORS middleware
- Structured logging
"""

from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
from datetime import datetime

from src.config import get_settings
from src.api.routes.agent import router as agent_router
from src.api.routes.websocket import router as websocket_router
from src.utils.database import close_mongo_connection, close_redis_connection
from src.utils.task_store import get_task_store

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiter instance
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    settings = get_settings()
    
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("=" * 60)
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"Debug Mode: {settings.debug}")
    logger.info("Rate limiting: 10 requests/minute for agent endpoints")
    
    # Verify Redis connection
    try:
        task_store = get_task_store()
        logger.info("✓ Redis task store connected")
    except Exception as e:
        logger.warning(f"⚠ Redis unavailable, using in-memory fallback: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    await close_redis_connection()
    
    # Close task store
    try:
        task_store = get_task_store()
        task_store.close()
    except Exception:
        pass
    
    logger.info("Cleanup complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
# PeerAgent Multi-Agent System API

A sophisticated multi-agent system built with LangGraph for intelligent task routing and execution.

## Features

- **Intelligent Routing**: Automatically routes tasks to the appropriate agent
- **Code Generation**: Generate clean, documented code in multiple languages
- **Content Research**: Web search with source citations
- **Business Analysis**: Socratic questioning for problem diagnosis
- **Problem Structuring**: Create structured problem trees
- **WebSocket Support**: Real-time communication for business Q&A
- **Rate Limiting**: 10 requests/minute per IP for agent endpoints

## Agents

| Agent | Description |
|-------|-------------|
| **PeerAgent** | Master orchestrator that routes to sub-agents |
| **CodeAgent** | Code generation and explanation |
| **ContentAgent** | Web research with citations |
| **BusinessSenseAgent** | Business problem diagnosis |
| **ProblemStructuringAgent** | Problem tree construction |

## WebSocket Endpoints

- `ws://host/ws/business/{session_id}` - Real-time business Q&A
- `ws://host/ws/agent/{session_id}` - General agent communication

## Quick Start

```bash
# Execute a task
curl -X POST http://localhost:8000/v1/agent/execute \\
  -H "Content-Type: application/json" \\
  -d '{"task": "Write a Python function to sort a list"}'

# Get task status
curl http://localhost:8000/v1/agent/status/{task_id}
```
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        swagger_ui_parameters={"defaultModelsExpandDepth": -1}
    )
    
    # Add rate limiter to app state
    app.state.limiter = limiter
    
    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.debug else None,
                "code": "INTERNAL_ERROR"
            }
        )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins if hasattr(settings, 'cors_origins') else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(agent_router, prefix=settings.api_prefix)
    app.include_router(websocket_router)  # WebSocket routes
    
    # Health check endpoint (no rate limit)
    @app.get("/health", tags=["Health"])
    async def health_check() -> Dict[str, Any]:
        """
        Comprehensive health check endpoint.
        
        Checks:
        - API server status
        - Redis connectivity
        - MongoDB connectivity
        """
        health_status = {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }
        
        # Check Redis
        try:
            task_store = get_task_store()
            if hasattr(task_store, 'redis'):
                task_store.redis.ping()
                health_status["checks"]["redis"] = "healthy"
            else:
                health_status["checks"]["redis"] = "in-memory fallback"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"
        
        # Check MongoDB
        try:
            from src.utils.database import get_mongo_client
            client = await get_mongo_client()
            await client.admin.command('ping')
            health_status["checks"]["mongodb"] = "healthy"
        except Exception as e:
            health_status["checks"]["mongodb"] = f"unhealthy: {e}"
            health_status["status"] = "degraded"
        
        return health_status
    
    # Simple health check (for load balancers)
    @app.get("/ping", tags=["Health"])
    async def ping():
        """Simple ping endpoint for load balancers."""
        return {"pong": True}
    
    # Root endpoint (no rate limit)
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "api_prefix": settings.api_prefix,
            "rate_limit": "10 requests/minute for /v1/agent/* endpoints",
            "websocket_endpoints": [
                "/ws/business/{session_id}",
                "/ws/agent/{session_id}"
            ]
        }
    
    # API info endpoint
    @app.get("/api/info", tags=["Root"])
    async def api_info():
        """Get detailed API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "api_version": "v1",
            "endpoints": {
                "execute": f"{settings.api_prefix}/agent/execute",
                "execute_async": f"{settings.api_prefix}/agent/execute/async",
                "status": f"{settings.api_prefix}/agent/status/{{task_id}}",
                "direct": f"{settings.api_prefix}/agent/execute/direct/{{agent_type}}",
                "classify": f"{settings.api_prefix}/agent/classify",
                "business_continue": f"{settings.api_prefix}/agent/business/continue",
                "tasks_list": f"{settings.api_prefix}/agent/tasks",
                "stats": f"{settings.api_prefix}/agent/stats"
            },
            "websocket_endpoints": {
                "business": "/ws/business/{session_id}",
                "agent": "/ws/agent/{session_id}"
            },
            "agent_types": ["code", "content", "business", "problem"],
            "rate_limits": {
                "execute": "10/minute",
                "status": "30/minute",
                "default": "60/minute"
            },
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
