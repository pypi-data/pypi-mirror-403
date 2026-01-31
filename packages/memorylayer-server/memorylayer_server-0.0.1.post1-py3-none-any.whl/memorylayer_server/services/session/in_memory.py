"""Default session service implementation."""
from datetime import datetime, timezone
from logging import Logger
from typing import Optional, Any

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import SessionServicePluginBase, SessionService
from ...models import Session, SessionContext


class InMemorySessionService(SessionService):
    """
    In-memory session management service.

    Sessions are temporary by design and use TTL-based expiration.
    All data is stored in memory and lost on service restart.
    """

    def __init__(self):
        """Initialize in-memory session storage."""
        # Store sessions: {workspace_id:session_id -> Session}
        self._sessions: dict[str, Session] = {}
        # Store contexts: {workspace_id:session_id -> {key -> SessionContext}}
        self._contexts: dict[str, dict[str, SessionContext]] = {}
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info("Initialized SessionService with in-memory storage")

    def _make_key(self, workspace_id: str, session_id: str) -> str:
        """Create composite key for session storage."""
        return f"{workspace_id}:{session_id}"

    async def create_session(self, workspace_id: str, session: Session) -> Session:
        """
        Store a new session.

        Args:
            workspace_id: Workspace identifier
            session: Session object to store

        Returns:
            The stored session

        Note:
            If a session with the same ID already exists, it will be replaced.
        """
        key = self._make_key(workspace_id, session.id)
        self._sessions[key] = session
        # Initialize empty context dict for this session
        self._contexts[key] = {}
        self.logger.info("Created session: %s in workspace: %s", session.id, workspace_id)
        return session

    async def get_session(self, workspace_id: str, session_id: str) -> Optional[Session]:
        """
        Retrieve session if it exists and has not expired.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier

        Returns:
            Session object if found and not expired, None otherwise

        Note:
            Expired sessions are automatically removed when accessed.
        """
        key = self._make_key(workspace_id, session_id)
        session = self._sessions.get(key)

        if session is None:
            self.logger.debug("Session not found: %s in workspace: %s", session_id, workspace_id)
            return None

        # Check expiration
        if session.is_expired:
            self.logger.info("Session expired: %s in workspace: %s, removing", session_id, workspace_id)
            # Clean up expired session
            await self.delete_session(workspace_id, session_id)
            return None

        self.logger.debug("Retrieved session: %s in workspace: %s", session_id, workspace_id)
        return session

    async def delete_session(self, workspace_id: str, session_id: str) -> bool:
        """
        Delete session and all its context entries.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier

        Returns:
            True if session was deleted, False if it didn't exist
        """
        key = self._make_key(workspace_id, session_id)

        # Remove session
        session_existed = key in self._sessions
        if session_existed:
            del self._sessions[key]

        # Remove all context entries
        if key in self._contexts:
            del self._contexts[key]

        if session_existed:
            self.logger.info("Deleted session: %s in workspace: %s", session_id, workspace_id)
        else:
            self.logger.debug("Session not found for deletion: %s in workspace: %s", session_id, workspace_id)

        return session_existed

    async def set_context(
            self,
            workspace_id: str,
            session_id: str,
            key: str,
            value: Any,
            ttl_seconds: Optional[int] = None
    ) -> SessionContext:
        """
        Set a context key-value pair within a session.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier
            key: Context key
            value: Context value (must be JSON-serializable)
            ttl_seconds: Optional TTL override (inherits from session if None)

        Returns:
            The created/updated SessionContext

        Raises:
            ValueError: If session doesn't exist or has expired
        """
        # Verify session exists and is not expired
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found or expired in workspace {workspace_id}")

        session_key = self._make_key(workspace_id, session_id)

        # Get or initialize context dict for this session
        if session_key not in self._contexts:
            self._contexts[session_key] = {}

        # Check if updating existing context
        existing = self._contexts[session_key].get(key)
        now = datetime.now(timezone.utc)

        if existing:
            # Update existing context
            context = SessionContext(
                session_id=session_id,
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
                created_at=existing.created_at,
                updated_at=now
            )
            self.logger.debug("Updated context key: %s in session: %s", key, session_id)
        else:
            # Create new context
            context = SessionContext(
                session_id=session_id,
                key=key,
                value=value,
                ttl_seconds=ttl_seconds,
                created_at=now,
                updated_at=now
            )
            self.logger.debug("Created context key: %s in session: %s", key, session_id)

        self._contexts[session_key][key] = context
        return context

    async def get_context(
            self,
            workspace_id: str,
            session_id: str,
            key: str
    ) -> Optional[SessionContext]:
        """
        Get a specific context entry.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier
            key: Context key

        Returns:
            SessionContext if found, None if session expired or key doesn't exist
        """
        # Verify session exists and is not expired
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            return None

        session_key = self._make_key(workspace_id, session_id)
        contexts = self._contexts.get(session_key, {})
        context = contexts.get(key)

        if context:
            self.logger.debug("Retrieved context key: %s from session: %s", key, session_id)
        else:
            self.logger.debug("Context key not found: %s in session: %s", key, session_id)

        return context

    async def get_all_context(
            self,
            workspace_id: str,
            session_id: str
    ) -> list[SessionContext]:
        """
        Get all context entries for a session.

        Args:
            workspace_id: Workspace identifier
            session_id: Session identifier

        Returns:
            List of SessionContext objects (empty if session expired or has no context)
        """
        # Verify session exists and is not expired
        session = await self.get_session(workspace_id, session_id)
        if session is None:
            return []

        session_key = self._make_key(workspace_id, session_id)
        contexts = self._contexts.get(session_key, {})

        self.logger.debug(
            "Retrieved %d context entries from session: %s",
            len(contexts),
            session_id
        )

        return list(contexts.values())


class InMemorySessionServicePlugin(SessionServicePluginBase):
    """Default session service plugin."""
    PROVIDER_NAME = 'in-memory'

    def initialize(self, v: Variables, logger: Logger) -> SessionService:
        return InMemorySessionService()
