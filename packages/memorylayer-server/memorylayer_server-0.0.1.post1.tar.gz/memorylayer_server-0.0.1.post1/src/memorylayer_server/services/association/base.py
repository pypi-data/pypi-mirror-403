from scitrera_app_framework.api import Plugin, Variables, enabled_option_pattern

from ...config import MEMORYLAYER_ASSOCIATION_SERVICE, DEFAULT_MEMORYLAYER_ASSOCIATION_SERVICE
from ..storage import EXT_STORAGE

# Extension point constant
EXT_ASSOCIATION_SERVICE = 'memorylayer-association-service'


# noinspection PyAbstractClass
class AssociationServicePluginBase(Plugin):
    """Base plugin for association service - allows SaaS to extend/override."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_ASSOCIATION_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_ASSOCIATION_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(self, v, MEMORYLAYER_ASSOCIATION_SERVICE,
                                      default=DEFAULT_MEMORYLAYER_ASSOCIATION_SERVICE,
                                      self_attr='PROVIDER_NAME')

    def get_dependencies(self, v: Variables):
        return (EXT_STORAGE,)
