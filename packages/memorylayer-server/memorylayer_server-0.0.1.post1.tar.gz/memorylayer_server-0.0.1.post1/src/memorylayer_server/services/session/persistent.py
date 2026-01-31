"""Persistent session service using storage backend."""
from datetime import datetime, timezone
from logging import Logger
from typing import Optional, Any

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import SessionServicePluginBase, SessionService
from ..storage import StorageBackend, EXT_STORAGE
from ...models import Session, SessionContext


class PersistentSessionService(SessionService):
    """Storage-backed session service.

    Sessions persist across server restarts using the configured
    StorageBackend (SQLite, PostgreSQL, etc.).

    This is the recommended session service for production deployments
    where session data should survive server restarts.
    """

    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info("Initialized PersistentSessionService with storage backend")

    async def create_session(self, workspace_id: str, session: Session) -> Session:
        """Store a new session in storage backend."""
        return await self.storage.create_session(workspace_id, session)

    async def get_session(self, workspace_id: str, session_id: str) -> Optional[Session]:
        """Retrieve session from storage if not expired."""
        return await self.storage.get_session(workspace_id, session_id)

    async def delete_session(self, workspace_id: str, session_id: str) -> bool:
        """Delete session and all context from storage."""
        return await self.storage.delete_session(workspace_id, session_id)

    async def set_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> SessionContext:
        """Set context in storage backend."""
        # Verify session exists
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found or expired")

        return await self.storage.set_session_context(
            workspace_id, session_id, key, value, ttl_seconds
        )

    async def get_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str
    ) -> Optional[SessionContext]:
        """Get context from storage backend."""
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            return None

        return await self.storage.get_session_context(workspace_id, session_id, key)

    async def get_all_context(
        self,
        workspace_id: str,
        session_id: str
    ) -> list[SessionContext]:
        """Get all context from storage backend."""
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            return []

        return await self.storage.get_all_session_context(workspace_id, session_id)

    async def cleanup_expired(self, workspace_id: str) -> int:
        """Cleanup expired sessions. Should be called periodically."""
        count = await self.storage.cleanup_expired_sessions(workspace_id)
        if count > 0:
            self.logger.info("Cleaned up %d expired sessions in workspace %s", count, workspace_id)
        return count


class PersistentSessionServicePlugin(SessionServicePluginBase):
    """Plugin for persistent session service."""
    PROVIDER_NAME = 'default'

    def get_dependencies(self, v: Variables):
        return (EXT_STORAGE,)

    def initialize(self, v: Variables, logger: Logger) -> SessionService:
        storage: StorageBackend = self.get_extension(EXT_STORAGE, v)
        return PersistentSessionService(storage=storage)
