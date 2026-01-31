"""Services package for MemoryLayer.

This package provides all core services using the plugin dependency injection pattern from scitrera-app-framework.
"""

# Import service packages (triggers their plugin registration)
from .storage import (
    StorageBackend, get_storage_backend, EXT_STORAGE,
)
from .embedding import (
    EmbeddingProvider, EmbeddingService, get_embedding_provider, get_embedding_service, EXT_EMBEDDING_SERVICE, EXT_EMBEDDING_PROVIDER,
)

from .association import (
    get_association_service, AssociationService,
    EXT_ASSOCIATION_SERVICE, AssociationServicePluginBase
)
from .memory import (
    get_memory_service, MemoryService,
    EXT_MEMORY_SERVICE, MemoryServicePluginBase
)
from .reflect import (
    get_reflect_service, ReflectService,
    EXT_REFLECT_SERVICE, ReflectServicePluginBase
)
from .session import (
    get_session_service, SessionService,
    EXT_SESSION_SERVICE, SessionServicePluginBase
)
from .workspace import (
    get_workspace_service, WorkspaceService,
    EXT_WORKSPACE_SERVICE, WorkspaceServicePluginBase
)
from .authorization import (
    get_authorization_service, AuthorizationService,
    EXT_AUTHORIZATION_SERVICE, AuthorizationServicePluginBase,
)
from .llm import (
    get_llm_service, get_llm_provider, LLMProvider,
    EXT_LLM_SERVICE, EXT_LLM_PROVIDER, LLMServicePluginBase, LLMProviderPluginBase,
    LLMNotConfiguredError,
)

from .cache import (
    get_cache_service, CacheService,
    EXT_CACHE_SERVICE, CacheServicePluginBase,
)

__all__ = (
    # Storage
    'StorageBackend',
    'get_storage_backend',
    'EXT_STORAGE',
    # Embedding
    'EmbeddingService',
    'EmbeddingProvider',
    'get_embedding_service',
    'get_embedding_provider',
    'EXT_EMBEDDING_PROVIDER',
    # Association
    'AssociationService',
    'get_association_service',
    'EXT_ASSOCIATION_SERVICE',
    'AssociationServicePluginBase',
    # Memory
    'MemoryService',
    'get_memory_service',
    'EXT_MEMORY_SERVICE',
    'MemoryServicePluginBase',
    # Reflect
    'ReflectService',
    'get_reflect_service',
    'EXT_REFLECT_SERVICE',
    'ReflectServicePluginBase',
    # Session
    'SessionService',
    'get_session_service',
    'EXT_SESSION_SERVICE',
    'SessionServicePluginBase',
    # Workspace
    'WorkspaceService',
    'get_workspace_service',
    'EXT_WORKSPACE_SERVICE',
    'WorkspaceServicePluginBase',
    # Authorization
    'AuthorizationService',
    'get_authorization_service',
    'EXT_AUTHORIZATION_SERVICE',
    'AuthorizationServicePluginBase',
    # LLM
    'LLMProvider',
    'get_llm_service',
    'get_llm_provider',
    'EXT_LLM_SERVICE',
    'EXT_LLM_PROVIDER',
    'LLMServicePluginBase',
    'LLMProviderPluginBase',
    'LLMNotConfiguredError',
    # Cache
    'CacheService',
    'get_cache_service',
    'EXT_CACHE_SERVICE',
    'CacheServicePluginBase',
)
