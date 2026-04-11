"""Dual-mode entry point: CLI + MCP Server for RememberMe.

Usage:
    python -m rememberme           -> MCP mode (stdio)
    python -m rememberme mcp       -> MCP mode (explicit)
    python -m rememberme --help     -> CLI help
    python -m rememberme add ...   -> CLI mode
    python -m rememberme search ... -> CLI mode
"""

from __future__ import annotations

import sys


def _should_use_mcp_mode(args: list[str]) -> bool:
    """Determine if we should run in MCP mode.

    MCP mode when:
    - No arguments provided (stdio mode)
    - First argument is 'mcp'
    """
    if len(args) <= 1:
        return True  # No args = MCP mode (stdio)
    return args[1] == "mcp"


def _run_mcp_mode() -> None:
    """Run as MCP server."""
    import asyncio
    from .mcp.adapter import run_mcp_mode
    asyncio.run(run_mcp_mode())


def _run_cli_mode() -> None:
    """Run as CLI application."""
    from .cli.commands import cli
    cli()


def main() -> None:
    """Main entry point with mode auto-detection."""
    if _should_use_mcp_mode(sys.argv):
        _run_mcp_mode()
    else:
        _run_cli_mode()


if __name__ == "__main__":
    main()
