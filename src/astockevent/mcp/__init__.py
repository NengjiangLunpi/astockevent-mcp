"""AStockEvent MCP Server — Model Context Protocol server for AI Agent consumption.

Provides 16 tools (via REST API proxy, zero local DB dependency).
See docs/api-contract.md for full tool listing.
All tools are read-only — no mutations, no side effects.

Usage:
    python -m astockevent.mcp          # Start MCP stdio server
    astockevent-mcp                    # CLI entry point
"""

import asyncio
import sys


def run() -> None:
    """CLI entry point for ``astockevent-mcp`` command."""
    from astockevent.mcp.stdio_server import main
    sys.exit(asyncio.run(main()))
