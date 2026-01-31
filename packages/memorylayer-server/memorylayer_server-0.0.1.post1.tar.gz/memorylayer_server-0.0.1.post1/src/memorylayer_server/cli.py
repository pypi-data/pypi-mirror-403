"""MemoryLayer.ai CLI - Command line interface for memory infrastructure."""

import click

from scitrera_app_framework import get_variables


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """MemoryLayer.ai - Memory infrastructure for LLM-powered agents."""
    from memorylayer_server.dependencies import preconfigure
    preconfigure()


@cli.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool):
    """Start the HTTP REST API server."""
    import uvicorn
    from memorylayer_server.config import (
        MEMORYLAYER_SERVER_HOST, MEMORYLAYER_SERVER_PORT, DEFAULT_MEMORYLAYER_SERVER_HOST, DEFAULT_MEMORYLAYER_SERVER_PORT
    )
    from memorylayer_server.main import app

    v = get_variables()
    if host is None:
        host = v.environ(MEMORYLAYER_SERVER_HOST, default=DEFAULT_MEMORYLAYER_SERVER_HOST)
    if port is None:
        port = v.environ(MEMORYLAYER_SERVER_PORT, default=DEFAULT_MEMORYLAYER_SERVER_PORT, type_fn=int)

    click.echo(f"Starting MemoryLayer.ai server on {host}:{port}")
    uvicorn.run(
        "memorylayer_server.main:app" if reload else app,
        host=host,
        port=port,
        reload=reload,
    )


@cli.command()
def mcp():
    """Start the MCP server (stdio mode for Claude/LLM integration)."""
    click.echo("Starting MemoryLayer.ai MCP server...", err=True)

    from memorylayer_server.mcp.server import run_mcp_server
    run_mcp_server()


@cli.command()
def version():
    """Show version information."""
    from memorylayer import __version__
    click.echo(f"MemoryLayer.ai v{__version__}")


@cli.command()
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]))
def info(output_format: str):
    """Show system information and configuration."""

    # TODO: load plugins, etc. to get accurate settings (i.e. make sure defaults are populated)

    get_variables()

    from memorylayer_server.config import get_settings

    settings = get_settings()

    if output_format == "json":
        import json
        # Convert settings to dict, excluding sensitive fields
        info_dict = {
            "profile": settings.profile.value,
            "embedding_provider": settings.embedding_provider.value,
            "embedding_model": settings.embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "api_host": settings.api_host,
            "api_port": settings.api_port,
            "log_level": settings.log_level,
            "mcp_tool_profile": settings.mcp_tool_profile,
        }
        if settings.data_dir:
            info_dict["data_dir"] = str(settings.data_dir)
        click.echo(json.dumps(info_dict, indent=2))
    else:
        click.echo("MemoryLayer.ai Configuration")
        click.echo("=" * 40)
        click.echo(f"Profile:            {settings.profile.value}")
        click.echo(f"Embedding Provider: {settings.embedding_provider.value}")
        click.echo(f"Embedding Model:    {settings.embedding_model}")
        click.echo(f"Embedding Dims:     {settings.embedding_dimensions}")
        click.echo(f"API Host:           {settings.api_host}")
        click.echo(f"API Port:           {settings.api_port}")
        click.echo(f"Log Level:          {settings.log_level}")
        click.echo(f"MCP Tools:          {settings.mcp_tool_profile}")
        if settings.data_dir:
            click.echo(f"Data Directory:     {settings.data_dir}")


if __name__ == "__main__":
    cli()
