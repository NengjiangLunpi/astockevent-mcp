"""AStockEvent MCP Server — stdio 传输层.

启动: python -m astockevent.mcp.stdio_server
协议: Model Context Protocol (2024-11-05), stdio transport
用途: Claude Desktop / VSCode / 任何 MCP-compatible AI Agent 直接调用
"""

import json
import sys
import logging
from typing import Any

from astockevent.mcp.server import (
    check_events,
    search_events_by_stock,
    search_events_by_type,
    search_events_by_shareholder,
    get_event_detail,
    get_event_timeline,
    get_upcoming_events,
    search_events,
    search_dividend_events,
    search_violation_events,
    search_restructuring_events,
    search_shareholder_events,
    search_risk_events,
    search_regulatory_events,
    get_trust_report,
    dispatch_tool_call,
)

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("astockevent-mcp")

SERVER_NAME = "astockevent"
SERVER_VERSION = "0.2.0"

TOOLS = [
    # ── Tool 1: search_events_by_stock ──
    {
        "name": "search_events_by_stock",
        "description": (
            "Query structured A-share announcement events by stock code(s). "
            "Returns events for: share_reduction (减持), delisting_risk (ST/退市), "
            "regulatory_letter (监管函/问询函), lockup_expiration (限售解禁), share_buyback (回购). "
            "Each event includes: event_id, event_type, stock_code, stock_name, ai_summary, "
            "confidence_tier, structured_payload, and announcement_date. "
            "Use when: you know the stock code(s) and want to check recent events for those stocks. "
            "Use this for portfolio monitoring, watchlist scanning, or single-stock deep dives. "
            "Do NOT use when: you want to search by event type across all stocks "
            "(use search_events_by_type), or when you need a specific shareholder's events "
            "(use search_events_by_shareholder). "
            "Supports cursor-based pagination — use the `cursor` field in the response "
            "to fetch the next page. "
            "Returns: {data: [...], cursor: <next_cursor_or_null>, has_more: bool}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "Comma-separated 6-digit stock codes. Example: '002272,600519,300750'.",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by event status. Options: active, updating, closed, corrected, archived. Empty = active + updating.",
                },
                "confidence_tier": {
                    "type": "string",
                    "description": "Filter by confidence tier. Options: verified, likely, uncertain. Empty = all.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor from previous response. Leave empty for first page.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results per page. Default: 20, Max: 200.",
                    "default": 20,
                },
            },
            "required": ["stock_codes"],
        },
        "annotations": {
            "title": "Search Events by Stock — query events for specific stock codes",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 2: search_events_by_type ──
    {
        "name": "search_events_by_type",
        "description": (
            "Query structured A-share announcement events by event type(s). "
            "Event types: share_reduction, delisting_risk, regulatory_letter, "
            "lockup_expiration, share_buyback. "
            "Use when: you want to find all events of a specific type across the market — "
            "e.g. all recent share reductions, all ST/delisting warnings, all regulatory letters. "
            "Do NOT use when: you know the stock code(s) (use search_events_by_stock), "
            "or when you need a complex multi-filter query (use search_events). "
            "Supports cursor-based pagination — use the `cursor` field in the response "
            "to fetch the next page. "
            "Returns: {data: [...], cursor: <next_cursor_or_null>, has_more: bool}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_types": {
                    "type": "string",
                    "description": "Comma-separated event types. Example: 'share_reduction,delisting_risk'.",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by event status. Options: active, updating, closed, corrected, archived.",
                },
                "confidence_tier": {
                    "type": "string",
                    "description": "Filter by confidence tier. Options: verified, likely, uncertain.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor from previous response. Leave empty for first page.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results per page. Default: 20, Max: 200.",
                    "default": 20,
                },
            },
            "required": ["event_types"],
        },
        "annotations": {
            "title": "Search Events by Type — query events by category",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 3: search_events_by_shareholder ──
    {
        "name": "search_events_by_shareholder",
        "description": (
            "Query events by shareholder name. Searches across all event types "
            "where the shareholder name appears in structured_payload. "
            "Most useful for: share_reduction (减持) events where shareholder_name "
            "is a top-level field in structured_payload. "
            "Use when: you want to track a specific shareholder's activity — "
            "e.g. '罗丽华' or '国家集成电路产业投资基金'. "
            "Do NOT use when: you want all events for a stock (use search_events_by_stock), "
            "or when you're unsure of the exact shareholder name "
            "(use search_events with keyword in ai_summary). "
            "Returns: {data: [...], cursor: <next_cursor_or_null>, has_more: bool}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "shareholder_name": {
                    "type": "string",
                    "description": "Exact shareholder name to search for. Example: '罗丽华'.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor from previous response.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results per page. Default: 20, Max: 200.",
                    "default": 20,
                },
            },
            "required": ["shareholder_name"],
        },
        "annotations": {
            "title": "Search Events by Shareholder — track specific shareholders",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 4: get_event_detail ──
    {
        "name": "get_event_detail",
        "description": (
            "Get the full detail for a single event by its event_id. "
            "Returns ALL fields: event metadata, structured_payload (quantitative fields "
            "specific to the event type), quantitative_tags, confidence_reasons, "
            "source info, timeline array, related events, and ai_summary. "
            "Use when: you have an event_id and need the complete event record — "
            "including type-specific fields in structured_payload that are not shown "
            "in list/search results. "
            "Do NOT use when: you only need the timeline (use get_event_timeline), "
            "or when you want to browse/search (use search_events_by_stock/type). "
            "Returns a single event object with all fields, or null if not found."
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
        "annotations": {
            "title": "Get Event Detail — full event record with structured payload",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 5: get_event_timeline ──
    {
        "name": "get_event_timeline",
        "description": (
            "Get the lifecycle timeline and full detail for a single event. "
            "Tracks the event through its lifecycle: plan → in_progress → completed/terminated. "
            "Returns: full event detail + timeline array (each entry has date, phase, description) "
            "+ related event IDs. "
            "Use when: you want to see the phase transitions and lifecycle history of an event "
            "you already know the event_id for. "
            "Do NOT use when: you want to search or browse events "
            "(use search_events_by_stock/type), or when you only need the summary fields "
            "(search_events_by_stock already returns ai_summary and key fields). "
            "Returns a single event object with timeline, or null if event_id is invalid or not found."
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
        "annotations": {
            "title": "Get Event Timeline — lifecycle tracking for a single event",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 6: get_upcoming_events ──
    {
        "name": "get_upcoming_events",
        "description": (
            "Get events due within the next N days — early warning for expirations and deadlines. "
            "Covers: lockup share expiration dates (限售股解禁到期), share reduction plan deadlines (减持计划到期), "
            "delisting period end dates (退市整理期结束), buyback implementation deadlines (回购实施到期), "
            "and regulatory letter reply deadlines (监管函回复截止日). "
            "Each result includes: event_id, event_type, stock_code, stock_name, "
            "due_date (ISO 8601 date, YYYY-MM-DD), days_remaining (integer countdown), and ai_summary. "
            "Use when: you need a forward-looking calendar — what lockup expirations, regulatory deadlines, "
            "or buyback periods are ending soon. "
            "Do NOT use when: you need historical event data or events without a future due date "
            "(use search_events_by_stock/type for general event queries). "
            "Returns a JSON array of upcoming events, ordered by due_date ascending (soonest first). "
            "Max look-ahead: 30 days. Only events with status=active|updating are included."
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
        "annotations": {
            "title": "Get Upcoming Events — early warning for expirations and deadlines",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 7: search_events (universal escape hatch — DEV-59) ──
    {
        "name": "search_events",
        "description": (
            "Universal event search with all supported filters. "
            "This is the escape hatch for complex queries not covered by the specialized tools. "
            "Supports all filter combinations: stock_code, event_type, since (datetime), "
            "status, confidence_tier, shareholder_name. "
            "Use when: you need a multi-filter query that doesn't fit into the specialized tools — "
            "e.g. 'all verified share_reduction events for 002272 since 2026-05-01'. "
            "Do NOT use when: a specialized tool (search_events_by_stock, search_events_by_type, "
            "search_events_by_shareholder) would work — prefer specialized tools for better results. "
            "Supports cursor-based pagination. "
            "Returns: {data: [...], cursor: <next_cursor_or_null>, has_more: bool}."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {
                    "type": "string",
                    "description": "Comma-separated 6-digit stock codes. Empty = all.",
                },
                "event_types": {
                    "type": "string",
                    "description": "Comma-separated event types. Empty = all.",
                },
                "event_type": {
                    "type": "string",
                    "description": "Single event type (backward-compat alias for event_types). Merged with event_types if both provided.",
                },
                "severity": {
                    "type": "string",
                    "description": "Filter by AI context severity: red, yellow, green. Comma-separated for multiple. Requires ai_context from DEV-84.",
                },
                "sentiment": {
                    "type": "string",
                    "description": "Filter by AI context sentiment: positive, negative, neutral. Comma-separated for multiple. Requires ai_context from DEV-84.",
                },
                "since": {
                    "type": "string",
                    "description": "ISO 8601 datetime or YYYY-MM-DD. Filter events updated after this time.",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by event status: active, updating, closed, corrected, archived.",
                },
                "confidence_tier": {
                    "type": "string",
                    "description": "Filter by confidence: verified, likely, uncertain.",
                },
                "shareholder_name": {
                    "type": "string",
                    "description": "Filter by shareholder name in structured_payload.",
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor from previous response.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results per page. Default: 20, Max: 200.",
                    "default": 20,
                },
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Events — universal escape hatch for complex queries",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── Tool 8: get_trust_report (PO-14e) ──
    {
        "name": "get_trust_report",
        "description": (
            "Get a trust and verification report for a single event. "
            "Returns: confidence_tier + confidence_score (heuristic 0-1), "
            "multi-source cross-validation details (which sources agree/disagree), "
            "and extraction quality metrics from the review system "
            "(regex vs LLM conflict count, llm_validation status, whether human-reviewed). "
            "Use when: you need to assess how reliable or trustworthy an event's extraction is — "
            "e.g. before making a trading decision based on the event data. "
            "Do NOT use when: you only need the event data itself (use get_event_detail), "
            "or when browsing/searching (use search_events_by_* tools). "
            "Returns a trust report object: {event_id, confidence_tier, confidence_score, "
            "confidence_reasons, cross_validation: {sources_checked, sources_agree, "
            "sources_disagree, source_details}, extraction_quality: {total_fields_reviewed, "
            "regex_llm_conflicts, llm_validation, human_reviewed}}."
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
        "annotations": {
            "title": "Get Trust Report — verify event extraction reliability",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    },
    # ── DEV-87b: 6 Specialized event search tools ──
    {
        "name": "search_dividend_events",
        "description": "Search dividend events (分红/送转). Pre-filtered to dividend. Use for dividend announcements, ex-rights dates, payout ratios.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Dividend Events — dividend announcements",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
        },
    },
    {
        "name": "search_violation_events",
        "description": "Search violation & penalty events (违规处罚/立案调查). Use for regulatory violations, investigations, penalties, fines.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Violation Events — regulatory penalties",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
        },
    },
    {
        "name": "search_restructuring_events",
        "description": "Search asset restructuring events (重大资产重组). Use for M&A, asset injections, spin-offs, reverse mergers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Restructuring Events — M&A activity",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
        },
    },
    {
        "name": "search_shareholder_events",
        "description": "Search shareholder behavior events (减持/增持/回购/质押). Covers share_reduction, share_increase, share_buyback, pledge_risk. Use for insider signals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Shareholder Events — insider activity",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
        },
    },
    {
        "name": "search_risk_events",
        "description": "Search risk events (ST/退市风险/质押风险/停复牌/限售解禁). Covers delisting_risk, pledge_risk, trading_halt_resume, lockup_expiration. Use for early warning signals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Risk Events — early warning signals",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
        },
    },
    {
        "name": "search_regulatory_events",
        "description": "Search regulatory events (监管函/问询函). Covers regulatory_letter, violation_penalty. Use for regulatory scrutiny signals from exchanges.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stock_codes": {"type": "string", "description": "Comma-separated stock codes. Empty = all."},
                "status": {"type": "string", "description": "Filter by event status."},
                "cursor": {"type": "string", "description": "Pagination cursor."},
                "limit": {"type": "integer", "description": "Max results. Default: 20.", "default": 20},
            },
            "required": [],
        },
        "annotations": {
            "title": "Search Regulatory Events — exchange scrutiny",
            "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True,
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
    """Dispatch a tools/call request to the shared handler in server.py."""
    params = msg.get("params", {})
    return await dispatch_tool_call(
        tool_name=params.get("name", ""),
        arguments=params.get("arguments", {}),
    )


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
