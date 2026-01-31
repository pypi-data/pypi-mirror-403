"""LLM service package."""
from .base import (
    LLMProvider,
    LLMProviderPluginBase,
    LLMServicePluginBase,
    EXT_LLM_PROVIDER,
    EXT_LLM_SERVICE,
)
from .service_default import LLMService
from .noop import LLMNotConfiguredError

from scitrera_app_framework import Variables, get_extension


def get_llm_provider(v: Variables = None) -> LLMProvider:
    """Get the LLM provider instance."""
    return get_extension(EXT_LLM_PROVIDER, v)


def get_llm_service(v: Variables = None) -> LLMService:
    """Get the LLM service instance."""
    return get_extension(EXT_LLM_SERVICE, v)


__all__ = (
    'LLMProvider',
    'LLMProviderPluginBase',
    'LLMService',
    'LLMServicePluginBase',
    'get_llm_provider',
    'get_llm_service',
    'EXT_LLM_PROVIDER',
    'EXT_LLM_SERVICE',
    'LLMNotConfiguredError',
)
