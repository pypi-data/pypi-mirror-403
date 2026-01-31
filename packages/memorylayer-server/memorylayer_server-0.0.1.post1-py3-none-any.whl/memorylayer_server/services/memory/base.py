from scitrera_app_framework.api import Plugin, Variables, enabled_option_pattern

from ...config import MEMORYLAYER_MEMORY_SERVICE, DEFAULT_MEMORYLAYER_MEMORY_SERVICE
from ..storage import EXT_STORAGE
from ..embedding import EXT_EMBEDDING_PROVIDER

# Extension point constant
EXT_MEMORY_SERVICE = 'memorylayer-memory-service'


# noinspection PyAbstractClass
class MemoryServicePluginBase(Plugin):
    """Base plugin for memory service - allows SaaS to extend/override."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_MEMORY_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_MEMORY_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_MEMORY_SERVICE,
                                      default=DEFAULT_MEMORYLAYER_MEMORY_SERVICE,
                                      self_attr='PROVIDER_NAME')

    def get_dependencies(self, v: Variables):
        return EXT_STORAGE, EXT_EMBEDDING_PROVIDER
