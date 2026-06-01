"""DataPulseX MCP Server — stdio 传输层.

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
            "检查指定股票池在指定时间段内的结构化公告事件。"
            "返回减持计划、ST/退市风险、监管函件、限售股解禁、股份回购等结构化 Event JSON。"
            "每个 Event 包含 event_id, event_type, stock_code, stock_name, ai_summary, "
            "confidence_tier, structured_payload 等字段。"
            "不返回主观评级，只返回量化事实。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "6位股票代码列表，逗号分隔。例如 '002272,600519,300750'",
                },
                "event_types": {
                    "type": "string",
                    "description": "事件类型过滤，逗号分隔。可选: share_reduction,delisting_risk,regulatory_letter,lockup_expiration,share_buyback",
                },
                "since": {
                    "type": "string",
                    "description": "起始日期 YYYY-MM-DD，默认 7 天前",
                },
                "limit": {
                    "type": "integer",
                    "description": "最大返回数，默认 50，最大 200",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_event_timeline",
        "description": (
            "获取单个事件的完整生命周期时间线。"
            "追踪事件从 plan → in_progress → completed/terminated 的全过程。"
            "返回事件详情 + timeline 数组（每个条目包含 date, phase, description）+ 关联事件列表。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_id": {
                    "type": "string",
                    "description": "Event UUID，例如 'dp_c8a7f9e1-d2b4-4a3c-8d5e-1f6a9b3c7d4e'",
                },
            },
            "required": ["event_id"],
        },
    },
    {
        "name": "get_upcoming_events",
        "description": (
            "获取未来N天内即将发生的事件。"
            "包括：限售股解禁日、减持计划到期日、退市整理期届满日、回购实施截止日、问询函回复截止日。"
            "每条返回 event_id, event_type, stock_code, due_date, days_remaining, ai_summary。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "6位股票代码列表，逗号分隔。不填=全市场",
                },
                "days": {
                    "type": "integer",
                    "description": "未来天数，默认 7，最大 30",
                    "default": 7,
                },
                "event_types": {
                    "type": "string",
                    "description": "事件类型过滤，逗号分隔",
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
    logger.info("DataPulseX MCP Server v%s starting on stdio", SERVER_VERSION)

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
