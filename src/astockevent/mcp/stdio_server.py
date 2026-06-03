"""AStockEvent MCP Server — stdio 传输层.

启动: python -m astockevent.mcp.stdio_server
协议: Model Context Protocol (2024-11-05), stdio transport
用途: Claude Desktop / VSCode / 任何 MCP-compatible AI Agent 直接调用
"""

import json
import sys
import logging
from typing import Any

from astockevent.mcp.server import check_events, get_event_timeline, get_upcoming_events

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("astockevent-mcp")

SERVER_NAME = "astockevent"
SERVER_VERSION = "0.1.0"

TOOLS = [
    {
        "name": "check_events",
        "description": (
            "Query structured announcement events for a watchlist of stocks within a time window. "
            "Returns structured Event JSON for share reductions, ST/delisting risks, regulatory letters, "
            "lockup expirations, and share buybacks. "
            "Each event includes: event_id, event_type, stock_code, stock_name, ai_summary, "
            "confidence_tier (verified|likely|uncertain), structured_payload (quantitative tags), "
            "and announcement_date. "
            "Use when: you need to check recent events for specific stocks, scan a watchlist, "
            "or filter by event type and date range. "
            "Do NOT use when: you need real-time stock prices, trading signals, or subjective ratings "
            "(this tool only returns structured facts from public announcements). "
            "Returns a JSON array of event objects, newest first."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "Comma-separated 6-digit stock codes. Example: '002272,600519,300750'. Empty = all stocks.",
                },
                "event_types": {
                    "type": "string",
                    "description": "Comma-separated event types to filter. Options: share_reduction, delisting_risk, regulatory_letter, lockup_expiration, share_buyback. Empty = all types.",
                },
                "since": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Default: 7 days ago.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return. Default: 50, Max: 200.",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_event_timeline",
        "description": (
            "Get the complete lifecycle timeline for a single event. "
            "Tracks the event through its full lifecycle: plan → in_progress → completed/terminated. "
            "Returns: event details + timeline array (each entry has date, phase, description) + "
            "related event IDs. "
            "Use when: you have an event_id and want to see its full history, phase transitions, "
            "and related events. "
            "Do NOT use when: you want to search or browse events (use check_events instead). "
            "Returns a single event object with timeline, or null if event_id not found."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event UUID v4. Example: 'c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e'",
                },
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "get_upcoming_events",
        "description": (
            "Get events due within the next N days (early warning). "
            "Covers: lockup share expiration dates, share reduction plan deadlines, "
            "delisting period end dates, buyback implementation deadlines, "
            "and regulatory letter reply deadlines. "
            "Each result includes: event_id, event_type, stock_code, stock_name, "
            "due_date, days_remaining, and ai_summary. "
            "Use when: you want to know what's coming up — expirations, deadlines, "
            "regulatory responses due. "
            "Do NOT use when: you need historical event data (use check_events). "
            "Returns a JSON array of upcoming events, ordered by due_date ascending."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "Comma-separated 6-digit stock codes. Empty = all stocks.",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead. Default: 7, Max: 30.",
                    "default": 7,
                },
                "event_types": {
                    "type": "string",
                    "description": "Comma-separated event types to filter. Empty = all types.",
                },
            },
            "required": [],
        },
    },
]


def _send(data: dict) -> None:
    """Write JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _handle_initialize(msg: dict) -> dict:
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "capabilities": {
            "tools": {},
        },
    }


def _handle_list_tools(_msg: dict) -> dict:
    return {"tools": TOOLS}


async def _handle_call_tool(msg: dict) -> dict:
    params = msg.get("params", {})
    tool_name = params.get("name", "")
    arguments = params.get("arguments", {})

    try:
        if tool_name == "check_events":
            result = await check_events(
                stock_codes=arguments.get("stock_codes", ""),
                event_types=arguments.get("event_types", ""),
                since=arguments.get("since", ""),
                limit=arguments.get("limit", 50),
            )
        elif tool_name == "get_event_timeline":
            result = await get_event_timeline(arguments.get("event_id", ""))
            if result is None:
                return {"content": [{"type": "text", "text": "Event not found"}]}
        elif tool_name == "get_upcoming_events":
            result = await get_upcoming_events(
                stock_codes=arguments.get("stock_codes", ""),
                days=arguments.get("days", 7),
                event_types=arguments.get("event_types", ""),
            )
        else:
            return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}]}

        return {
            "content": [
                {"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}
            ]
        }
    except Exception as e:
        logger.error("Tool %s failed: %s", tool_name, e)
        return {"content": [{"type": "text", "text": f"Error: {e}"}]}


async def main():
    """MCP stdio 主循环."""
    logger.info("AStockEvent MCP Server v%s starting on stdio", SERVER_VERSION)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        msg_id = msg.get("id")
        method = msg.get("method", "")

        if method == "initialize":
            resp = _handle_initialize(msg)
        elif method == "tools/list":
            resp = _handle_list_tools(msg)
        elif method == "tools/call":
            resp = await _handle_call_tool(msg)
        elif method == "notifications/initialized":
            continue  # No response needed
        else:
            resp = {"error": {"code": -32601, "message": f"Method not found: {method}"}}

        if msg_id is not None:
            if isinstance(resp, dict) and "error" in resp:
                _send({"jsonrpc": "2.0", "id": msg_id, "error": resp["error"]})
            else:
                _send({"jsonrpc": "2.0", "id": msg_id, "result": resp})


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
