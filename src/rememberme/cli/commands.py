"""Click CLI commands for RememberMe."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

# Lazy imports handled by entry point

logger = logging.getLogger(__name__)


def _setup_logging(debug: bool = False) -> None:
    """Configure logging with file rotation."""
    log_dir = Path.home() / ".remember-me" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if debug else logging.INFO
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.FileHandler(log_dir / "rememberme.log"),
            logging.StreamHandler(),
        ],
    )


@click.group()
@click.option("--user-id", "user_id", default=None, help="User ID scope")
@click.option("--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, user_id: str | None, debug: bool) -> None:
    """RememberMe - Long-term memory management CLI.

    Memory management for Claude Code with Qdrant vector storage.
    """
    ctx.ensure_object(dict)
    ctx.obj["user_id"] = user_id
    ctx.obj["debug"] = debug
    _setup_logging(debug)


@cli.command()
@click.argument("text")
@click.option("--agent-id", "agent_id", help="Session/run identifier")
@click.option("--json", "output_format", flag_value="json", default=False, help="JSON output")
@click.pass_context
def add(
    ctx: click.Context,
    text: str,
    agent_id: str | None,
    output_format: str,
) -> None:
    """Add a new memory.

    TEXT is the memory content to store.

    Example:

        remember-me add "User prefers dark mode"
    """
    from ..core.memory_manager import get_memory_manager
    from ..core.exceptions import QdrantOfflineError, ValidationError
    from .formatter import get_formatter

    manager = get_memory_manager()
    formatter = get_formatter(output_format)

    try:
        result = manager.add_memory(
            text=text,
            user_id=ctx.obj["user_id"],
            agent_id=agent_id,
        )
        click.echo(formatter.format_memory(result))
    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except QdrantOfflineError as e:
        click.echo(f"Qdrant Offline: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("query")
@click.option("--limit", default=5, help="Max results (default: 5)")
@click.option("--agent-id", "agent_id", help="Filter by session")
@click.option("--json", "output_format", flag_value="json", default=False, help="JSON output")
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    limit: int,
    agent_id: str | None,
    output_format: str,
) -> None:
    """Search memories by semantic similarity.

    QUERY is the search query text.

    Example:

        remember-me search "user preferences"
    """
    from ..core.memory_manager import get_memory_manager
    from ..core.exceptions import QdrantOfflineError, ValidationError
    from .formatter import get_formatter

    manager = get_memory_manager()
    formatter = get_formatter(output_format)

    try:
        result = manager.search_memories(
            query=query,
            user_id=ctx.obj["user_id"],
            agent_id=agent_id,
            limit=limit,
        )
        click.echo(formatter.format_search(result))
    except ValidationError as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    except QdrantOfflineError as e:
        click.echo(f"Qdrant Offline: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--json", "output_format", flag_value="json", default=False, help="JSON output")
@click.pass_context
def status(ctx: click.Context, output_format: str) -> None:
    """Check Qdrant connection and memory count.

    Example:

        remember-me status
    """
    from ..core.memory_manager import get_memory_manager
    from ..core.exceptions import QdrantOfflineError
    from .formatter import get_formatter

    manager = get_memory_manager()
    formatter = get_formatter(output_format)

    try:
        status_info = manager.get_status()
        status_dict = {
            "connected": status_info.connected,
            "host": status_info.host,
            "port": status_info.port,
            "collection": status_info.collection,
            "count": status_info.count,
        }
        click.echo(formatter.format_status(status_dict))
    except QdrantOfflineError as e:
        status_dict = {
            "connected": False,
            "error": str(e),
        }
        formatter = get_formatter(output_format)
        click.echo(formatter.format_status(status_dict), err=True)
        raise click.Abort()


@cli.command()
@click.argument("memory_id")
@click.pass_context
def delete(ctx: click.Context, memory_id: str) -> None:
    """Delete a memory by ID.

    MEMORY_ID is the UUID of the memory to delete.

    Example:

        remember-me delete 550e8400-e29b-41d4-a716-446655440000
    """
    from ..core.memory_manager import get_memory_manager
    from ..core.exceptions import QdrantOfflineError

    manager = get_memory_manager()

    try:
        result = manager.delete_memory(memory_id)
        if result:
            click.echo(f"Deleted memory: {memory_id}")
        else:
            click.echo(f"Memory not found: {memory_id}", err=True)
            raise click.Abort()
    except QdrantOfflineError as e:
        click.echo(f"Qdrant Offline: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--agent-id", "agent_id", help="Delete only memories for this session")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_all(ctx: click.Context, agent_id: str | None, force: bool) -> None:
    """Delete all memories for the current user.

    Use --agent-id to delete only memories for a specific session.
    Use --force to skip the confirmation prompt.

    Example:

        remember-me delete-all --force
    """
    from ..core.memory_manager import get_memory_manager
    from ..core.exceptions import QdrantOfflineError

    user_id = ctx.obj["user_id"]
    manager = get_memory_manager()

    if not force:
        user_part = f" for user '{user_id}'" if user_id else ""
        agent_part = f" in session '{agent_id}'" if agent_id else ""
        confirmed = click.confirm(
            f"Delete all memories{user_part}{agent_part}? This cannot be undone."
        )
        if not confirmed:
            click.echo("Cancelled.")
            return

    try:
        count = manager.delete_all_memories(user_id=user_id, agent_id=agent_id)
        click.echo(f"Deleted {count} memories.")
    except QdrantOfflineError as e:
        click.echo(f"Qdrant Offline: {e}", err=True)
        raise click.Abort()


def main() -> None:
    """Entry point for CLI mode."""
    cli()


if __name__ == "__main__":
    main()
