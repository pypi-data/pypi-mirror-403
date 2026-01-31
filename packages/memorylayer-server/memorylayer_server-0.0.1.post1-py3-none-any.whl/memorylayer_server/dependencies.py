"""dependency injection for MemoryLayer.ai.

Uses scitrera-app-framework plugin pattern for service initialization.
Services are lazily initialized on first access via get_extension().
"""
from contextlib import asynccontextmanager
from logging import Logger

from scitrera_app_framework import Variables, get_variables, get_logger, init_framework_desktop
from .config import MEMORYLAYER_DATA_DIR

_preconfigure_hooks: list = []


# noinspection PyTypeHints
def preconfigure(v: Variables = None, test_mode: bool = False, test_logger: Logger = None) -> (Variables, dict):
    """ Pre-configure the framework """
    additional_kwargs = {} if not test_mode else {
        'fault_handler': False,
        'fixed_logger': test_logger,
        'pyroscope': False,
        'shutdown_hooks': False,
    }
    v: Variables = init_framework_desktop(
        'memorylayer-server',
        base_plugins=False, stateful_chdir=True, stateful_root_env_key=MEMORYLAYER_DATA_DIR,
        v=v, **additional_kwargs)
    logger = get_logger(v)
    # Import services module to trigger plugin registration

    logger.debug('Registering core services')
    from scitrera_app_framework import register_package_plugins
    from . import services  # noqa: F401

    # register package plugins
    register_package_plugins(services.__package__, v, recursive=True)

    logger.debug('Evaluating preconfigure hooks')
    global _preconfigure_hooks
    if v.get('__preconfigure_hooks_installed__', default=False):
        return v, services

    # TODO: run through preconfigure hooks (allows for registering additional plugins before initialization)
    #       (note: we should have a flag mechanism to prevent duplicate running through the preconfigure hooks)

    v.set('__preconfigure_hooks_installed__', True)
    logger.debug('Installed preconfiguration hooks')
    return v, services


async def initialize_services(v: Variables = None) -> Variables:
    """Initialize all services on application startup."""

    # ensure preconfigured
    v, services = preconfigure(v)
    logger = get_logger(v)

    logger.debug("Initializing services")

    # Connect storage backend (async initialization)
    storage = services.get_storage_backend(v)
    await storage.connect()
    logger.info("Storage backend connected")

    return v


async def shutdown_services(v: Variables = None) -> None:
    """Shutdown all services on application shutdown."""
    from .services.storage import get_storage_backend

    v = get_variables(v)
    logger = get_logger(v)

    logger.debug("Shutting down services")

    try:
        storage = get_storage_backend(v)
        await storage.disconnect()
        logger.info("Disconnected storage backend")
    except Exception as e:
        logger.error("Error disconnecting storage backend: %s", e)


@asynccontextmanager
async def lifespan_context():
    """Application lifespan context manager."""
    v: Variables = await initialize_services()
    try:
        yield
    finally:
        await shutdown_services(v)
