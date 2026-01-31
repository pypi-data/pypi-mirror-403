"""Authorization Service - Pluggable permission checking interface."""
from abc import ABC, abstractmethod
from typing import Optional

from scitrera_app_framework.api import Plugin, Variables, enabled_option_pattern

from ...config import MEMORYLAYER_AUTHORIZATION_SERVICE, DEFAULT_MEMORYLAYER_AUTHORIZATION_SERVICE
from ...models.authz import AuthorizationDecision, AuthorizationContext

EXT_AUTHORIZATION_SERVICE = 'memorylayer-authorization-service'


class AuthorizationService(ABC):
    """Abstract authorization service interface.

    This is the pluggable authorization layer for MemoryLayer.

    The OSS default (OpenPermissionsAuthorizationService) allows all operations.
    SaaS/Enterprise implementations can provide RBAC, tenant isolation, etc.
    """

    @abstractmethod
    async def authorize(self, context: AuthorizationContext) -> AuthorizationDecision:
        """Check if the operation is authorized.

        Args:
            context: Authorization context with tenant/workspace/user/resource/action

        Returns:
            AuthorizationDecision.ALLOW, DENY, or ABSTAIN
        """
        pass

    @abstractmethod
    async def get_allowed_workspaces(
            self,
            tenant_id: str,
            user_id: str
    ) -> list[str]:
        """Get list of workspace IDs user can access.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier

        Returns:
            List of workspace IDs (empty = no access, ['*'] = all workspaces)
        """
        pass

    @abstractmethod
    async def get_user_role(
            self,
            tenant_id: str,
            workspace_id: str,
            user_id: str
    ) -> Optional[str]:
        """Get user's role in a workspace.

        Args:
            tenant_id: Tenant identifier
            workspace_id: Workspace identifier
            user_id: User identifier

        Returns:
            Role string (admin, developer, reader) or None if no access
        """
        pass


# noinspection PyAbstractClass
class AuthorizationServicePluginBase(Plugin):
    """Base plugin for authorization service."""
    PROVIDER_NAME: str = None

    def name(self) -> str:
        return f"{EXT_AUTHORIZATION_SERVICE}|{self.PROVIDER_NAME}"

    def extension_point_name(self, v: Variables) -> str:
        return EXT_AUTHORIZATION_SERVICE

    def is_enabled(self, v: Variables) -> bool:
        return enabled_option_pattern(
            self, v,
            MEMORYLAYER_AUTHORIZATION_SERVICE,
            default=DEFAULT_MEMORYLAYER_AUTHORIZATION_SERVICE,
            self_attr='PROVIDER_NAME'
        )
