"""Entry point for ``python -m astockevent.mcp``."""
import asyncio
import sys

if __name__ == "__main__":
    from astockevent.mcp.stdio_server import main
    sys.exit(asyncio.run(main()))
