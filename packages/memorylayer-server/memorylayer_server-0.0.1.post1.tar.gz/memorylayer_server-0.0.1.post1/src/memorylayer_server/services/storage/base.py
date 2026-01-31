"""Abstract storage backend interface."""
from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Optional, Any

from scitrera_app_framework import get_logger, get_extension
from scitrera_app_framework.api import Variables, Plugin, enabled_option_pattern

from ...config import MEMORYLAYER_STORAGE_BACKEND, DEFAULT_MEMORYLAYER_STORAGE_BACKEND

from ...models.memory import Memory, RememberInput, RecallInput, RecallResult
from ...models.association import Association, AssociateInput, GraphQueryInput, GraphQueryResult
from ...models.workspace import Workspace, MemorySpace
from ...models.resource import Resource
from ...models.category import Category

if TYPE_CHECKING:
    from ...models import Session, SessionContext

EXT_STORAGE = 'memorylayer-primary-storage'


class StorageBackend(ABC):
    """
    Abstract base class for storage backends.
    """

    def __init__(self):
        self.logger = get_logger(name=self.__class__.__name__)

    # Lifecycle
    @abstractmethod
    async def connect(self) -> None:
        """Initialize storage connection."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close storage connection."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if storage is healthy."""
        pass

    # Memory operations
    @abstractmethod
    async def create_memory(self, workspace_id: str, input: RememberInput) -> Memory:
        """Store a new memory."""
        pass

    @abstractmethod
    async def get_memory(self, workspace_id: str, memory_id: str) -> Optional[Memory]:
        """Get memory by ID."""
        pass

    @abstractmethod
    async def update_memory(self, workspace_id: str, memory_id: str, **updates) -> Optional[Memory]:
        """Update memory fields."""
        pass

    @abstractmethod
    async def delete_memory(self, workspace_id: str, memory_id: str, hard: bool = False) -> bool:
        """Soft or hard delete memory."""
        pass

    @abstractmethod
    async def search_memories(
            self,
            workspace_id: str,
            query_embedding: list[float],
            limit: int = 10,
            min_relevance: float = 0.5,
            types: Optional[list[str]] = None,
            subtypes: Optional[list[str]] = None,
            tags: Optional[list[str]] = None,
    ) -> list[tuple[Memory, float]]:
        """Vector similarity search, returns (memory, relevance_score) tuples."""
        pass

    @abstractmethod
    async def full_text_search(
            self,
            workspace_id: str,
            query: str,
            limit: int = 10,
    ) -> list[Memory]:
        """Full-text search on memory content."""
        pass

    @abstractmethod
    async def get_memory_by_hash(self, workspace_id: str, content_hash: str) -> Optional[Memory]:
        """Get memory by content hash for deduplication."""
        pass

    # Association operations
    @abstractmethod
    async def create_association(self, workspace_id: str, input: AssociateInput) -> Association:
        """Create graph edge between memories."""
        pass

    @abstractmethod
    async def get_associations(
            self,
            workspace_id: str,
            memory_id: str,
            direction: str = "both",  # outgoing, incoming, both
            relationships: Optional[list[str]] = None,
    ) -> list[Association]:
        """Get associations for a memory."""
        pass

    @abstractmethod
    async def traverse_graph(
            self,
            workspace_id: str,
            start_id: str,
            max_depth: int = 3,
            relationships: Optional[list[str]] = None,
            direction: str = "both",
    ) -> GraphQueryResult:
        """Multi-hop graph traversal."""
        pass

    # Workspace operations
    @abstractmethod
    async def create_workspace(self, workspace: Workspace) -> Workspace:
        """Create workspace."""
        pass

    @abstractmethod
    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        pass

    # Memory Space operations
    @abstractmethod
    async def create_memory_space(self, workspace_id: str, space: MemorySpace) -> MemorySpace:
        """Create a memory space within a workspace."""
        pass

    @abstractmethod
    async def get_memory_space(self, workspace_id: str, space_id: str) -> Optional[MemorySpace]:
        """Get memory space by ID."""
        pass

    @abstractmethod
    async def list_memory_spaces(self, workspace_id: str) -> list[MemorySpace]:
        """List all memory spaces in a workspace."""
        pass

    # Resource operations
    @abstractmethod
    async def create_resource(self, workspace_id: str, resource: Resource) -> Resource:
        """Store raw resource."""
        pass

    @abstractmethod
    async def get_resource(self, workspace_id: str, resource_id: str) -> Optional[Resource]:
        """Get resource by ID."""
        pass

    # Category operations
    @abstractmethod
    async def get_or_create_category(self, workspace_id: str, name: str) -> Category:
        """Get existing or create new category."""
        pass

    @abstractmethod
    async def update_category_summary(
            self,
            workspace_id: str,
            category_id: str,
            summary: str,
            item_ids: list[str]
    ) -> Category:
        """Update category summary."""
        pass

    # Statistics
    @abstractmethod
    async def get_workspace_stats(self, workspace_id: str) -> dict:
        """Get memory statistics for workspace."""
        pass

    # Session operations (for persistent sessions)
    @abstractmethod
    async def create_session(self, workspace_id: str, session: 'Session') -> 'Session':
        """Store a new session."""
        pass

    @abstractmethod
    async def get_session(self, workspace_id: str, session_id: str) -> Optional['Session']:
        """Get session by ID (returns None if not found or expired)."""
        pass

    @abstractmethod
    async def delete_session(self, workspace_id: str, session_id: str) -> bool:
        """Delete session and all its context."""
        pass

    @abstractmethod
    async def set_session_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> 'SessionContext':
        """Set context key-value within session."""
        pass

    @abstractmethod
    async def get_session_context(
        self,
        workspace_id: str,
        session_id: str,
        key: str
    ) -> Optional['SessionContext']:
        """Get specific context entry."""
        pass

    @abstractmethod
    async def get_all_session_context(
        self,
        workspace_id: str,
        session_id: str
    ) -> list['SessionContext']:
        """Get all context entries for session."""
        pass

    @abstractmethod
    async def cleanup_expired_sessions(self, workspace_id: str) -> int:
        """Delete all expired sessions. Returns number cleaned up."""
        pass


# noinspection PyAbstractClass
class StoragePluginBase(Plugin):
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_STORAGE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_STORAGE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_STORAGE_BACKEND, default=DEFAULT_MEMORYLAYER_STORAGE_BACKEND,
                                      self_attr='PROVIDER_NAME')

    def shutdown(self, v: Variables, logger: Logger, value: object | None) -> None:
        # TODO: support async shutdown [find correct loop and handle it there...]
        # if isinstance(value, StorageBackend):
        #     try:
        #         value.disconnect()
        #     except Exception as e:
        #         logger.error("Error disconnecting storage backend: %s", e)
        return


