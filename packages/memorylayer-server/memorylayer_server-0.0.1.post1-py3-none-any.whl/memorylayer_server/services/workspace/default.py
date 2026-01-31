"""Default workspace service implementation."""
import sqlite3
from logging import Logger
from typing import Optional

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from ...models import Workspace, MemorySpace
from ..storage import EXT_STORAGE, StorageBackend
from .base import WorkspaceServicePluginBase


class WorkspaceService:
    """
    Core workspace service implementing workspace and memory space operations.

    This service coordinates workspace and memory space management with
    storage backend integration.
    """

    def __init__(self, storage: StorageBackend):
        """
        Initialize workspace service.

        Args:
            storage: Storage backend for workspace persistence
        """
        self._storage = storage
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info("Initialized WorkspaceService")

    async def create_workspace(self, workspace: Workspace) -> Workspace:
        """
        Create a new workspace.

        Args:
            workspace: Workspace object to create

        Returns:
            Created workspace with generated fields

        Raises:
            ValueError: If workspace validation fails
        """
        self.logger.info(
            "Creating workspace: %s for tenant: %s",
            workspace.name,
            workspace.tenant_id
        )

        # Create workspace via storage backend
        created = await self._storage.create_workspace(workspace)

        self.logger.info("Created workspace: %s", created.id)
        return created

    async def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """
        Get workspace by ID.

        Args:
            workspace_id: Unique workspace identifier

        Returns:
            Workspace if found, None otherwise
        """
        self.logger.debug("Getting workspace: %s", workspace_id)
        return await self._storage.get_workspace(workspace_id)

    async def update_workspace(self, workspace: Workspace) -> Workspace:
        """
        Update workspace settings.

        Note: Storage backend may not have update_workspace yet, so we store
        the updated workspace directly via create_workspace (upsert behavior).

        Args:
            workspace: Workspace with updated fields

        Returns:
            Updated workspace

        Raises:
            ValueError: If workspace doesn't exist
        """
        self.logger.info("Updating workspace: %s", workspace.id)

        # Check if workspace exists
        existing = await self._storage.get_workspace(workspace.id)
        if not existing:
            raise ValueError(f"Workspace not found: {workspace.id}")

        # Storage backend doesn't have update_workspace yet, so we use create
        # (assuming upsert behavior - in production, this would be update_workspace)
        updated = await self._storage.create_workspace(workspace)

        self.logger.info("Updated workspace: %s", workspace.id)
        return updated

    async def create_memory_space(
            self,
            workspace_id: str,
            space: MemorySpace
    ) -> MemorySpace:
        """
        Create a memory space within a workspace.

        Args:
            workspace_id: Parent workspace ID
            space: Memory space to create

        Returns:
            Created memory space

        Raises:
            ValueError: If workspace doesn't exist or space name already exists
        """
        self.logger.info(
            "Creating memory space: %s in workspace: %s",
            space.name,
            workspace_id
        )

        # Verify workspace exists
        workspace = await self._storage.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        # Ensure space has workspace_id set correctly
        if space.workspace_id != workspace_id:
            self.logger.warning(
                "Memory space workspace_id mismatch, overriding %s with %s",
                space.workspace_id,
                workspace_id
            )
            # Create new space with correct workspace_id (MemorySpace is immutable)
            space = MemorySpace(
                id=space.id,
                workspace_id=workspace_id,
                name=space.name,
                description=space.description,
                settings=space.settings,
                created_at=space.created_at,
            )

        # Store via storage backend (DB constraint ensures uniqueness)
        try:
            created = await self._storage.create_memory_space(workspace_id, space)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint" in str(e):
                raise ValueError(
                    f"Memory space '{space.name}' already exists in workspace {workspace_id}"
                )
            raise

        self.logger.info("Created memory space: %s", created.id)
        return created

    async def list_memory_spaces(self, workspace_id: str) -> list[MemorySpace]:
        """
        List all memory spaces in a workspace.

        Args:
            workspace_id: Workspace ID to list spaces for

        Returns:
            List of memory spaces (empty list if none exist)

        Raises:
            ValueError: If workspace doesn't exist
        """
        self.logger.debug("Listing memory spaces for workspace: %s", workspace_id)

        # Verify workspace exists
        workspace = await self._storage.get_workspace(workspace_id)
        if not workspace:
            raise ValueError(f"Workspace not found: {workspace_id}")

        # Return spaces from storage backend
        spaces = await self._storage.list_memory_spaces(workspace_id)
        self.logger.debug("Found %d memory spaces", len(spaces))

        return spaces


class DefaultWorkspaceServicePlugin(WorkspaceServicePluginBase):
    """Default workspace service plugin."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> WorkspaceService:
        storage: StorageBackend = self.get_extension(EXT_STORAGE, v)
        return WorkspaceService(
            storage=storage,
        )
