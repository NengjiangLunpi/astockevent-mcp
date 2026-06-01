"""AStockEvent MCP Server — Model Context Protocol server for AI Agent consumption.

Provides 3 tools:
- check_events: Query structured announcement events by stock codes
- get_event_timeline: Get full lifecycle timeline for a single event
- get_upcoming_events: Get upcoming events within N days

Usage:
    python -m astockevent.mcp          # Start MCP stdio server
    python -m astockevent.mcp.stdio_server  # Same, explicitly
"""
