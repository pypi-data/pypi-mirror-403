"""
Working memory/session context API endpoints.

Endpoints:
- POST /v1/sessions - Create session
- GET /v1/sessions/{session_id} - Get session
- DELETE /v1/sessions/{session_id} - Delete session
- POST /v1/sessions/{session_id}/context - Set context key
- GET /v1/sessions/{session_id}/context - Get context
- GET /v1/sessions/briefing - Session briefing
"""
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status

from .schemas import (
    SessionCreateRequest,
    SessionContextSetRequest,
    SessionResponse,
    SessionContextResponse,
    SessionBriefingResponse,
    ErrorResponse,
)
from memorylayer_server.services.session import get_session_service as _get_session_service, SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])


def get_session_service() -> SessionService:
    """FastAPI dependency wrapper for session service."""
    return _get_session_service()


# Dependency to get workspace_id from auth context
async def get_workspace_id() -> str:
    """
    Get workspace ID from authentication context.

    In production, this would extract from JWT token or API key.
    For development, returns a default workspace ID.
    """
    # TODO: Implement actual auth
    return "default_workspace"




@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def create_session(
    request: SessionCreateRequest,
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> SessionResponse:
    """
    Create a new working memory session.

    Sessions provide TTL-based temporary context storage.

    Args:
        request: Session creation request
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Returns:
        Created session

    Raises:
        HTTPException: If session creation fails
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or f"sess_{uuid4().hex[:16]}"

        logger.info(
            "Creating session: %s in workspace: %s, ttl: %d",
            session_id,
            workspace_id,
            request.ttl_seconds
        )

        # Create session
        from ...models.session import Session
        session = Session.create_with_ttl(
            session_id=session_id,
            workspace_id=workspace_id,
            ttl_seconds=request.ttl_seconds,
            metadata=request.metadata,
        )

        # Store session via session service
        session = await session_service.create_session(workspace_id, session)

        logger.info("Created session: %s", session_id)
        return SessionResponse(session=session)

    except ValueError as e:
        logger.warning("Invalid session creation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Failed to create session: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session"
        )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found or expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_session(
    session_id: str,
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> SessionResponse:
    """
    Retrieve a session by ID.

    Args:
        session_id: Session identifier
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Returns:
        Session object

    Raises:
        HTTPException: If session not found or expired
    """
    try:
        logger.debug("Getting session: %s", session_id)

        session = await session_service.get_session(workspace_id, session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found or expired: {session_id}"
            )
        return SessionResponse(session=session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session %s: %s", session_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def delete_session(
    session_id: str,
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> None:
    """
    Delete a session and all its context data.

    Args:
        session_id: Session identifier
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Raises:
        HTTPException: If session not found or deletion fails
    """
    try:
        logger.info("Deleting session: %s", session_id)

        success = await session_service.delete_session(workspace_id, session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session %s: %s", session_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )


@router.post(
    "/{session_id}/context",
    response_model=SessionContextResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Session not found or expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def set_context(
    session_id: str,
    request: SessionContextSetRequest,
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> SessionContextResponse:
    """
    Set a key-value context entry in a session.

    Args:
        session_id: Session identifier
        request: Context set request
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Returns:
        Session context entry

    Raises:
        HTTPException: If session not found or context set fails
    """
    try:
        logger.info(
            "Setting context in session: %s, key: %s",
            session_id,
            request.key
        )

        context = await session_service.set_context(
            workspace_id=workspace_id,
            session_id=session_id,
            key=request.key,
            value=request.value,
            ttl_seconds=request.ttl_seconds,
        )
        return SessionContextResponse(
            key=context.key,
            value=context.value,
            ttl_seconds=context.ttl_seconds,
            created_at=context.created_at,
            updated_at=context.updated_at
        )

    except ValueError as e:
        logger.warning("Invalid context set request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to set context in session %s: %s",
            session_id,
            e,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set session context"
        )


@router.get(
    "/{session_id}/context",
    response_model=dict,
    responses={
        404: {"model": ErrorResponse, "description": "Session not found or expired"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_context(
    session_id: str,
    key: str | None = None,
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> dict:
    """
    Get session context data.

    Args:
        session_id: Session identifier
        key: Optional specific key to retrieve (returns all if omitted)
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Returns:
        Context data (single entry if key specified, all entries otherwise)

    Raises:
        HTTPException: If session not found
    """
    try:
        logger.debug("Getting context from session: %s, key: %s", session_id, key)

        if key:
            context = await session_service.get_context(workspace_id, session_id, key)
            if not context:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Context key not found: {key}"
                )
            return {key: context.value}
        else:
            contexts = await session_service.get_all_context(workspace_id, session_id)
            return {ctx.key: ctx.value for ctx in contexts}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get context from session %s: %s",
            session_id,
            e,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session context"
        )


@router.get(
    "/briefing",
    response_model=SessionBriefingResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def get_briefing(
    workspace_id: str = Depends(get_workspace_id),
    session_service=Depends(get_session_service),
) -> SessionBriefingResponse:
    """
    Get a briefing of recent workspace activity and context.

    Provides:
    - Workspace summary (total memories, recent activity)
    - Recent sessions and activity
    - Open threads/topics
    - Detected contradictions

    Args:
        workspace_id: Workspace ID from auth context
        session_service: Session service instance

    Returns:
        Session briefing with activity summary

    Raises:
        HTTPException: If briefing generation fails
    """
    try:
        logger.info("Generating briefing for workspace: %s", workspace_id)

        # TODO: Generate briefing via session service
        # briefing = await session_service.get_briefing(workspace_id)
        # return SessionBriefingResponse(briefing=briefing)

        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Session briefing not yet implemented"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to generate briefing: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate briefing"
        )
