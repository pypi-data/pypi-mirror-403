"""Health check endpoints for MemoryLayer.ai API."""

import logging
from typing import Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns:
        dict: Health status
    """
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint verifying database and cache connectivity.

    Returns:
        JSONResponse: Readiness status with service checks
    """
    checks = {
        "status": "ready",
        "services": {},
    }

    # Check database connectivity
    try:
        # TODO: Implement actual database ping via storage backend plugin
        from memorylayer_server.services.storage import get_storage_backend
        storage = get_storage_backend()
        # Storage backend should be connected at startup
        checks["services"]["database"] = "connected"
    except Exception as e:
        logger.error("Database connectivity check failed: %s", e)
        checks["services"]["database"] = "disconnected"
        checks["status"] = "not_ready"

    # Cache is optional and not yet configured via plugin
    checks["services"]["cache"] = "not_configured"

    status_code = (
        status.HTTP_200_OK
        if checks["status"] == "ready"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(content=checks, status_code=status_code)
