"""AStockEvent MCP Server — 16 Tools (REST API Proxy).

MCP Server for AI Agent consumption.
Thin proxy layer: MCP stdio → HTTP → AStockEvent REST API → PostgreSQL.
Zero database dependency — no SQLAlchemy, no psycopg2, no akshare.

Config:
  ASTOCKEVENT_API_URL  — REST API base URL (default: https://astockevent.com)
  ASTOCKEVENT_API_KEY  — API key for authenticated tier (optional; anonymous = free tier)

Tools (16 total, Phase 2):
  1. search_events_by_stock       — query by stock code(s)
  2. search_events_by_type        — query by event type(s)
  3. search_events_by_shareholder — query by shareholder name
  4. get_event_detail             — full event detail (was get_event_timeline)
  5. get_event_timeline           — timeline entries for an event
  6. get_upcoming_events          — upcoming deadlines (unchanged)
  7. search_events                — universal escape hatch (DEV-59)
  8. get_trust_report             — trust/verification report (PO-14e)
  9. search_dividend_events       — dividend events (DEV-87b)
 10. search_violation_events      — violation & penalty events (DEV-87b)
 11. search_restructuring_events  — asset restructuring events (DEV-87b)
 12. search_shareholder_events    — shareholder behavior events (DEV-87b)
 13. search_risk_events           — risk events (DEV-87b)
 14. search_regulatory_events     — regulatory events (DEV-87b)
 15. search_cb_events             — convertible bond events (G-21)
 16. search_fund_events           — fund penetration events (F-7)
"""

import json
import os
import logging
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("ASTOCKEVENT_API_URL", "https://astockevent.com").rstrip("/")
API_KEY = os.getenv("ASTOCKEVENT_API_KEY", "")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    """Build request headers. Includes API key if configured."""
    h = {"Accept": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def _api(path: str) -> str:
    return f"{API_BASE_URL}{path}"


def _event_to_mcp_dict(event: dict) -> dict:
    """Normalize an event dict from the REST API into MCP-friendly format.

    Flattens nested source objects, ensures required fields exist,
    and removes internal-only fields. AI agents receive clean, consistent dicts.
    """
    source = event.get("source", {}) or {}
    if isinstance(source, dict):
        source_name = source.get("primary", {}).get("name", "") or source.get("name", "")
    else:
        source_name = str(source)

    return {
        "event_id": event.get("event_id", ""),
        "event_type": event.get("event_type", ""),
        "stock_code": event.get("stock_code", ""),
        "stock_name": event.get("stock_name", ""),
        "market": event.get("market", ""),
        "status": event.get("status", ""),
        "phase": event.get("phase", ""),
        "confidence_tier": event.get("confidence_tier", ""),
        "confidence_reasons": event.get("confidence_reasons", []),
        "ai_summary": event.get("ai_summary", ""),
        "announcement_date": event.get("announcement_date", ""),
        "announcement_time": event.get("announcement_time"),
        "last_updated_at": event.get("last_updated_at", ""),
        "source": source_name,
        "source_url": event.get("source_url"),
        "structured_payload": event.get("structured_payload", {}),
        "quantitative_tags": event.get("quantitative_tags", {}),
        # EventDetail fields (only present in detail endpoint)
        "timeline": event.get("timeline", []),
        "related_events": event.get("related_events", []),
        "merge_parent": event.get("merge_parent"),
        "first_seen_at": event.get("first_seen_at"),
        "schema_version": event.get("schema_version", "0.1.0"),
        # DEV-84: AI context for agent consumption (severity, sentiment, etc.)
        "ai_context": event.get("ai_context"),
    }


async def _fetch_list(
    path: str,
    params: dict[str, str | int],
) -> dict:
    """Fetch a paginated list from the REST API and return normalized result."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_api(path), params=params, headers=_headers())
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("MCP API call failed [%s]: %s", path, exc)
        return {"data": [], "cursor": None, "has_more": False}

    if body.get("error"):
        logger.warning("MCP API error [%s]: %s", path, body["error"])
        return {"data": [], "cursor": None, "has_more": False}

    data = [_event_to_mcp_dict(e) for e in body.get("data", [])]
    meta = body.get("meta", {})
    return {
        "data": data,
        "cursor": meta.get("cursor"),
        "has_more": meta.get("has_more", False),
    }


# ---------------------------------------------------------------------------
# Tool 1: search_events_by_stock
# ---------------------------------------------------------------------------


async def search_events_by_stock(
    stock_codes: str,
    status: str = "",
    confidence_tier: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Query events by stock code(s). Use when you know the stock codes.

    Proxies to GET /v1/events?stock_code=... with cursor pagination.
    """
    params: dict[str, str | int] = {"limit": min(limit, 200)}
    if stock_codes:
        params["stock_code"] = stock_codes
    if status:
        params["status"] = status
    if confidence_tier:
        params["confidence_tier"] = confidence_tier
    if cursor:
        params["cursor"] = cursor

    return await _fetch_list("/v1/events", params)


# ---------------------------------------------------------------------------
# Tool 2: search_events_by_type
# ---------------------------------------------------------------------------


async def search_events_by_type(
    event_types: str,
    status: str = "",
    confidence_tier: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Query events by event type(s). Use when you know the event type.

    Proxies to GET /v1/events?event_type=... with cursor pagination.
    """
    params: dict[str, str | int] = {"limit": min(limit, 200)}
    if event_types:
        params["event_type"] = event_types
    if status:
        params["status"] = status
    if confidence_tier:
        params["confidence_tier"] = confidence_tier
    if cursor:
        params["cursor"] = cursor

    return await _fetch_list("/v1/events", params)


# ---------------------------------------------------------------------------
# Tool 3: search_events_by_shareholder
# ---------------------------------------------------------------------------


async def search_events_by_shareholder(
    shareholder_name: str,
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Query events by shareholder name. Use when investigating specific shareholders.

    Proxies to GET /v1/events?shareholder_name=... with cursor pagination.
    """
    params: dict[str, str | int] = {"limit": min(limit, 200)}
    if shareholder_name:
        params["shareholder_name"] = shareholder_name
    if cursor:
        params["cursor"] = cursor

    return await _fetch_list("/v1/events", params)


# ---------------------------------------------------------------------------
# Tool 4: get_event_detail
# ---------------------------------------------------------------------------


async def get_event_detail(event_id: str) -> dict | None:
    """Get full event detail including structured_payload and timeline.

    Proxies to GET /v1/events/{event_id}.
    """
    try:
        UUID(event_id)
    except ValueError:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_api(f"/v1/events/{event_id}"), headers=_headers())
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("get_event_detail: API call failed: %s", exc)
        return None

    if body.get("error"):
        logger.warning("get_event_detail: API error: %s", body["error"])
        return None

    return _event_to_mcp_dict(body.get("data", {}))


# ---------------------------------------------------------------------------
# Tool 5: get_event_timeline
# ---------------------------------------------------------------------------


async def get_event_timeline(event_id: str) -> dict | None:
    """Get timeline entries for a single event.

    Proxies to GET /v1/events/{event_id}/timeline.
    Returns the timeline array with phase transitions.
    """
    try:
        UUID(event_id)
    except ValueError:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                _api(f"/v1/events/{event_id}/timeline"), headers=_headers()
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("get_event_timeline: API call failed: %s", exc)
        return None

    if body.get("error"):
        logger.warning("get_event_timeline: API error: %s", body["error"])
        return None

    return _event_to_mcp_dict(body.get("data", {}))


# ---------------------------------------------------------------------------
# Tool 6: get_upcoming_events
# ---------------------------------------------------------------------------


async def get_upcoming_events(
    stock_codes: str = "",
    days: int = 7,
    event_types: str = "",
) -> list[dict]:
    """Get events due within the next N days (early warning).

    Proxies to GET /v1/events/upcoming.
    """
    params: dict[str, str | int] = {"days": min(days, 30)}
    if stock_codes:
        params["stock_code"] = stock_codes
    if event_types:
        params["event_type"] = event_types

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                _api("/v1/events/upcoming"), params=params, headers=_headers()
            )
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("get_upcoming_events: API call failed: %s", exc)
        return []

    if body.get("error"):
        logger.warning("get_upcoming_events: API error: %s", body["error"])
        return []
    return body.get("data", [])


# ---------------------------------------------------------------------------
# Tool 7: search_events (universal escape hatch — DEV-59)
# ---------------------------------------------------------------------------


async def search_events(
    stock_codes: str = "",
    event_types: str = "",
    event_type: str = "",
    since: str = "",
    status: str = "",
    confidence_tier: str = "",
    shareholder_name: str = "",
    cb_event_type: str = "",
    severity: str = "",
    sentiment: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Universal event search with all filters. Escape hatch for complex queries.

    Proxies to GET /v1/events with all supported filters + cursor pagination.
    DEV-87a: Added event_type (backward-compat alias for event_types),
    severity (red/yellow/green), sentiment (positive/negative/neutral) filters.
    D-28: cb_event_type filter for sub-type (call_redemption/put_resale/
    conversion_price_down/maturity) — use search_cb_events for cb-specific queries.
    """
    # DEV-87a: merge backward-compat event_type into event_types
    if event_type and not event_types:
        event_types = event_type
    elif event_type and event_types:
        existing = set(event_types.split(","))
        existing.add(event_type)
        event_types = ",".join(existing)

    params: dict[str, str | int] = {"limit": min(limit, 200)}
    if stock_codes:
        params["stock_code"] = stock_codes
    if event_types:
        params["event_type"] = event_types
    if since:
        params["since"] = since
    if status:
        params["status"] = status
    if confidence_tier:
        params["confidence_tier"] = confidence_tier
    if shareholder_name:
        params["shareholder_name"] = shareholder_name
    if cb_event_type:
        params["cb_event_type"] = cb_event_type
    if cursor:
        params["cursor"] = cursor

    result = await _fetch_list("/v1/events", params)

    # DEV-87a: Client-side severity/sentiment filtering (ai_context fields)
    if severity and result.get("data"):
        severities = set(s.strip().lower() for s in severity.split(","))
        result["data"] = [
            e for e in result["data"]
            if (e.get("ai_context") or {}).get("severity", "").lower() in severities
        ]
    if sentiment and result.get("data"):
        sentiments = set(s.strip().lower() for s in sentiment.split(","))
        result["data"] = [
            e for e in result["data"]
            if (e.get("ai_context") or {}).get("sentiment", "").lower() in sentiments
        ]

    return result


# ---------------------------------------------------------------------------
# Backward-compat alias: check_events → search_events
# ---------------------------------------------------------------------------


async def check_events(
    stock_codes: str = "",
    event_types: str = "",
    since: str = "",
    limit: int = 50,
) -> list[dict]:
    """[DEPRECATED] Backward-compat alias for search_events.

    Returns flat list of events (no cursor metadata) for existing MCP clients.
    """
    result = await search_events(
        stock_codes=stock_codes,
        event_types=event_types,
        since=since,
        limit=limit,
    )
    return result.get("data", [])


# ---------------------------------------------------------------------------
# DEV-87b: Specialized event search tools (6 per event category/domain)
# ---------------------------------------------------------------------------


async def search_dividend_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search dividend events (分红/送转). Pre-filtered to dividend event type.

    Use when: you want dividend announcements, ex-rights dates, payout ratios.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="dividend",
        status=status,
        cursor=cursor,
        limit=limit,
    )


async def search_violation_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search violation & penalty events (违规处罚/立案调查).

    Use when: you want regulatory violations, investigations, penalties.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="violation_penalty",
        status=status,
        cursor=cursor,
        limit=limit,
    )


async def search_restructuring_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search asset restructuring events (重大资产重组).

    Use when: you want M&A, asset injections, spin-offs.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="asset_restructuring",
        status=status,
        cursor=cursor,
        limit=limit,
    )


async def search_shareholder_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search shareholder behavior events (减持/增持/回购/质押).

    Covers: share_reduction, share_increase, share_buyback, pledge_risk.
    Use when: you want insider trading signals, shareholder activity.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="share_reduction,share_increase,share_buyback,pledge_risk",
        status=status,
        cursor=cursor,
        limit=limit,
    )


async def search_risk_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search risk events (ST/退市风险/质押风险/停复牌/限售解禁).

    Covers: delisting_risk, pledge_risk, trading_halt_resume, lockup_expiration.
    Use when: you want early warning signals for position risk management.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="delisting_risk,pledge_risk,trading_halt_resume,lockup_expiration",
        status=status,
        cursor=cursor,
        limit=limit,
    )


async def search_regulatory_events(
    stock_codes: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search regulatory events (监管函/问询函).

    Covers: regulatory_letter, violation_penalty.
    Use when: you want regulatory scrutiny signals from exchanges.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="regulatory_letter,violation_penalty",
        status=status,
        cursor=cursor,
        limit=limit,
    )


# ── Tool 15: search_cb_events (G-21: 可转债专用入口) ──


async def search_cb_events(
    stock_codes: str = "",
    cb_event_type: str = "",
    status: str = "",
    cursor: str = "",
    limit: int = 20,
) -> dict:
    """Search convertible bond events (可转债事件).

    Covers: call_redemption (强赎), put_resale (回售), conversion_price_down (下修), maturity (到期).
    Use when: you want convertible bond corporate action signals — forced redemption deadlines,
    put-back rights, conversion price adjustments, or maturity redemption.
    """
    return await search_events(
        stock_codes=stock_codes,
        event_types="cb_event",
        cb_event_type=cb_event_type,
        status=status,
        cursor=cursor,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Tool 8: get_trust_report (PO-14e)
# ---------------------------------------------------------------------------


async def get_trust_report(event_id: str) -> dict | None:
    """Get trust/verification report for a single event.

    Returns multi-source cross-validation details + extraction quality metrics.
    Use when: you need to assess how reliable an event's extraction is.
    Do NOT use when: you just need the event data itself (use get_event_detail).
    """
    try:
        UUID(event_id)
    except ValueError:
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                _api(f"/v1/events/{event_id}/trust-report"), headers=_headers()
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("get_trust_report: API call failed: %s", exc)
        return None

    if body.get("error"):
        logger.warning("get_trust_report: API error: %s", body["error"])
        return None

    return body.get("data", {})


# ── Tool 16: search_fund_events (F-7: 基金穿透事件) ──


async def search_fund_events(
    fund_code: str,
    event_types: str = "",
    days: int = 30,
    min_weight: float = 0.0,
) -> dict:
    """Search fund penetration events — cross-reference holdings with stock events.

    Input a fund code → get its underlying stock holdings → return weighted event feed
    sorted by impact_score = weight_pct × severity_weight.

    Proxies to GET /v1/funds/{fund_code}/events.
    """
    params: dict[str, str | int | float] = {"days": min(days, 90)}
    if event_types:
        params["event_types"] = event_types
    if min_weight > 0:
        params["min_weight"] = min_weight

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                _api(f"/v1/funds/{fund_code}/events"),
                params=params,
                headers=_headers(),
            )
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("search_fund_events: API call failed: %s", exc)
        return {"data": None, "error": str(exc)}

    if body.get("error"):
        logger.warning("search_fund_events: API error: %s", body["error"])
        return {"data": None, "error": body["error"]}

    return body.get("data", {})


# ---------------------------------------------------------------------------
# Shared tool-call dispatch (used by both stdio and HTTP transports)
# ---------------------------------------------------------------------------


async def dispatch_tool_call(tool_name: str, arguments: dict) -> dict:
    """Dispatch a tool call by name to the correct handler.

    Single source of truth for the if/elif tool dispatch chain.
    Used by both stdio_server.py and http_server.py — no more duplication.
    """
    try:
        # ── Backward-compat alias ──
        if tool_name == "check_events":
            result = await check_events(
                stock_codes=arguments.get("stock_codes", ""),
                event_types=arguments.get("event_types", ""),
                since=arguments.get("since", ""),
                limit=arguments.get("limit", 50),
            )
        # ── Tool 1: search_events_by_stock ──
        elif tool_name == "search_events_by_stock":
            result = await search_events_by_stock(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                confidence_tier=arguments.get("confidence_tier", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── Tool 2: search_events_by_type ──
        elif tool_name == "search_events_by_type":
            result = await search_events_by_type(
                event_types=arguments.get("event_types", ""),
                status=arguments.get("status", ""),
                confidence_tier=arguments.get("confidence_tier", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── Tool 3: search_events_by_shareholder ──
        elif tool_name == "search_events_by_shareholder":
            result = await search_events_by_shareholder(
                shareholder_name=arguments.get("shareholder_name", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── Tool 4: get_event_detail ──
        elif tool_name == "get_event_detail":
            result = await get_event_detail(arguments.get("event_id", ""))
            if result is None:
                return {"content": [{"type": "text", "text": "Event not found"}]}
        # ── Tool 5: get_event_timeline ──
        elif tool_name == "get_event_timeline":
            result = await get_event_timeline(arguments.get("event_id", ""))
            if result is None:
                return {"content": [{"type": "text", "text": "Event not found"}]}
        # ── Tool 6: get_upcoming_events ──
        elif tool_name == "get_upcoming_events":
            result = await get_upcoming_events(
                stock_codes=arguments.get("stock_codes", ""),
                days=arguments.get("days", 7),
                event_types=arguments.get("event_types", ""),
            )
        # ── Tool 7: search_events (universal escape hatch + DEV-87a) ──
        elif tool_name == "search_events":
            result = await search_events(
                stock_codes=arguments.get("stock_codes", ""),
                event_types=arguments.get("event_types", ""),
                event_type=arguments.get("event_type", ""),
                since=arguments.get("since", ""),
                status=arguments.get("status", ""),
                confidence_tier=arguments.get("confidence_tier", ""),
                shareholder_name=arguments.get("shareholder_name", ""),
                severity=arguments.get("severity", ""),
                sentiment=arguments.get("sentiment", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── DEV-87b: 6 specialized search tools ──
        elif tool_name == "search_dividend_events":
            result = await search_dividend_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        elif tool_name == "search_violation_events":
            result = await search_violation_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        elif tool_name == "search_restructuring_events":
            result = await search_restructuring_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        elif tool_name == "search_shareholder_events":
            result = await search_shareholder_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        elif tool_name == "search_risk_events":
            result = await search_risk_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        elif tool_name == "search_regulatory_events":
            result = await search_regulatory_events(
                stock_codes=arguments.get("stock_codes", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── Tool 15: search_cb_events (G-21) ──
        elif tool_name == "search_cb_events":
            result = await search_cb_events(
                stock_codes=arguments.get("stock_codes", ""),
                cb_event_type=arguments.get("cb_event_type", ""),
                status=arguments.get("status", ""),
                cursor=arguments.get("cursor", ""),
                limit=arguments.get("limit", 20),
            )
        # ── Tool 16: search_fund_events (F-7) ──
        elif tool_name == "search_fund_events":
            result = await search_fund_events(
                fund_code=arguments.get("fund_code", ""),
                event_types=arguments.get("event_types", ""),
                days=arguments.get("days", 30),
                min_weight=arguments.get("min_weight", 0.0),
            )
        # ── Tool 8: get_trust_report (PO-14e) ──
        elif tool_name == "get_trust_report":
            result = await get_trust_report(arguments.get("event_id", ""))
            if result is None:
                return {"content": [{"type": "text", "text": "Event not found"}]}
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
