# FastAPI Application - Main Entry Point
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.config import get_settings
from src.api.routes.agent import router as agent_router
from src.utils.database import close_mongo_connection, close_redis_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"LLM Provider: {settings.llm_provider}, Model: {settings.llm_model}")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await close_mongo_connection()
    await close_redis_connection()
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

## Agents

- **PeerAgent**: Master orchestrator that routes to sub-agents
- **CodeAgent**: Code generation and explanation
- **ContentAgent**: Web research with citations
- **BusinessSenseAgent**: Business problem diagnosis
- **ProblemStructuringAgent**: Problem tree construction
        """,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(agent_router, prefix=settings.api_prefix)
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
