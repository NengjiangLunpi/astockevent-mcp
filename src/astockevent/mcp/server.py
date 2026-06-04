"""AStockEvent MCP Server — 3 Tools (REST API Proxy).

MCP Server for AI Agent consumption.
Thin proxy layer: MCP stdio → HTTP → AStockEvent REST API → PostgreSQL.
Zero database dependency — no SQLAlchemy, no psycopg2, no akshare.

Config:
  ASTOCKEVENT_API_URL  — REST API base URL (default: http://8.210.73.193:8000)
  ASTOCKEVENT_API_KEY  — API key for authenticated tier (optional; anonymous = free tier)
"""

import os
import logging
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE_URL = os.getenv("ASTOCKEVENT_API_URL", "http://8.210.73.193:8000").rstrip("/")
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


# ---------------------------------------------------------------------------
# MCP Tool handlers
# ---------------------------------------------------------------------------


async def check_events(
    stock_codes: str = "",
    event_types: str = "",
    since: str = "",
    limit: int = 50,
) -> list[dict]:
    """MCP Tool 1: Query structured announcement events for a watchlist.

    Proxies to GET /v1/events.
    """
    params: dict[str, str | int] = {"limit": min(limit, 200)}
    if stock_codes:
        params["stock_code"] = stock_codes
    if event_types:
        params["event_type"] = event_types
    if since:
        params["since"] = since

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_api("/v1/events"), params=params, headers=_headers())
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("check_events: API call failed: %s", exc)
        return []

    if body.get("error"):
        logger.warning("check_events: API error: %s", body["error"])
        return []
    return body.get("data", [])


async def get_event_timeline(event_id: str) -> dict | None:
    """MCP Tool 2: Get full lifecycle timeline for a single event.

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
        logger.error("get_event_timeline: API call failed: %s", exc)
        return None

    if body.get("error"):
        logger.warning("get_event_timeline: API error: %s", body["error"])
        return None
    return body.get("data")


async def get_upcoming_events(
    stock_codes: str = "",
    days: int = 7,
    event_types: str = "",
) -> list[dict]:
    """MCP Tool 3: Get events due within the next N days (early warning).

    Proxies to GET /v1/events/upcoming.
    """
    params: dict[str, str | int] = {"days": min(days, 30)}
    if stock_codes:
        params["stock_code"] = stock_codes
    if event_types:
        params["event_type"] = event_types

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(_api("/v1/events/upcoming"), params=params, headers=_headers())
            resp.raise_for_status()
            body = resp.json()
    except httpx.HTTPError as exc:
        logger.error("get_upcoming_events: API call failed: %s", exc)
        return []

    if body.get("error"):
        logger.warning("get_upcoming_events: API error: %s", body["error"])
        return []
    return body.get("data", [])
