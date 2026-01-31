"""FastAPI application for MemoryLayer.ai."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api.v1 import associations, memories, workspaces, health, sessions

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown tasks.

    Args:
        app: FastAPI application instance

    Yields:
        None: Control to the application
    """
    from .dependencies import initialize_services, shutdown_services

    logger.info("Starting MemoryLayer.ai API v%s", __version__)

    # Initialize services (storage, embedding, memory service)
    await initialize_services()

    logger.info("Application startup complete")

    yield

    # Shutdown tasks
    logger.info("Shutting down MemoryLayer.ai API")

    # Shutdown services
    await shutdown_services()

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="MemoryLayer.ai API",
    description="API-first memory infrastructure for LLM-powered agents",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])

# API v1 routers
app.include_router(memories.router, prefix="/v1")
app.include_router(associations.router, prefix="/v1")
app.include_router(sessions.router, prefix="/v1")
app.include_router(workspaces.router, prefix="/v1")


@app.get("/")
async def root() -> dict:
    """
    Root endpoint providing API information.

    Returns:
        dict: API name and version
    """
    return {
        "name": "MemoryLayer.ai",
        "version": __version__,
        "description": "API-first memory infrastructure for LLM-powered agents",
    }
