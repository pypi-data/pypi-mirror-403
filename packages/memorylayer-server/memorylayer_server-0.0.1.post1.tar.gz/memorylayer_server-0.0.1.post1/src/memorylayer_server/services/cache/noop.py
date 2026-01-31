"""No-op cache service - always returns None (OSS default)."""
from logging import Logger
from typing import Optional, Any

from scitrera_app_framework import get_logger
from scitrera_app_framework.api import Variables

from .base import CacheService, CacheServicePluginBase


class NoOpCacheService(CacheService):
    """Default cache that does nothing.

    OSS default - no caching overhead.
    SaaS can override with Redis, Memcached, etc.
    """

    def __init__(self):
        self.logger = get_logger(name=self.__class__.__name__)
        self.logger.info(
            "Initialized NoOpCacheService - caching disabled. "
            "Set MEMORYLAYER_CACHE_SERVICE to enable caching."
        )

    async def get(self, key: str) -> Optional[Any]:
        """Always returns None - no caching."""
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """No-op - returns True but doesn't cache."""
        return True

    async def delete(self, key: str) -> bool:
        """No-op - returns False (nothing to delete)."""
        return False

    async def exists(self, key: str) -> bool:
        """Always returns False - nothing cached."""
        return False

    async def clear_prefix(self, prefix: str) -> int:
        """No-op - returns 0."""
        return 0


class NoOpCacheServicePlugin(CacheServicePluginBase):
    """Plugin for no-op cache service."""
    PROVIDER_NAME = 'default'

    def initialize(self, v: Variables, logger: Logger) -> CacheService:
        return NoOpCacheService()
