"""
Session Service - Working memory management with TTL-based expiration.

This service manages temporary sessions and their context data in memory.
Sessions automatically expire based on their TTL and are not persisted to disk.

Operations:
- create_session: Register a new working memory session
- get_session: Retrieve session if not expired
- delete_session: Remove session and all its context
- set_context: Store key-value data within a session
- get_context: Retrieve specific context entry
- get_all_context: Get all context entries for a session
"""

from abc import ABC, abstractmethod
from typing import Optional, Any, List

from scitrera_app_framework.api import Plugin, Variables, enabled_option_pattern

from ...config import MEMORYLAYER_SESSION_SERVICE, DEFAULT_MEMORYLAYER_SESSION_SERVICE
from ...models import Session, SessionContext

# Extension point constant
EXT_SESSION_SERVICE = 'memorylayer-session-service'


class SessionService(ABC):
    """Interface for session service."""

    @abstractmethod
    async def create_session(self, workspace_id: str, session: Session) -> Session:
        """Store a new session."""
        pass

    @abstractmethod
    async def get_session(self, workspace_id: str, session_id: str) -> Optional[Session]:
        """Retrieve session if not expired."""
        pass

    @abstractmethod
    async def delete_session(self, workspace_id: str, session_id: str) -> bool:
        """Delete session and all its context."""
        pass

    @abstractmethod
    async def set_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> SessionContext:
        """Store key-value data within a session."""
        pass

    @abstractmethod
    async def get_context(self, workspace_id: str, session_id: str, key: str) -> Optional[SessionContext]:
        """Retrieve specific context entry."""
        pass

    @abstractmethod
    async def get_all_context(self, workspace_id: str, session_id: str) -> List[SessionContext]:
        """Get all context entries for a session."""
        pass


# noinspection PyAbstractClass
class SessionServicePluginBase(Plugin):
    """Base plugin for session service - allows SaaS to extend/override."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_SESSION_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_SESSION_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_SESSION_SERVICE,
                                      default=DEFAULT_MEMORYLAYER_SESSION_SERVICE,
                                      self_attr='PROVIDER_NAME')
