"""AStockEvent MCP Server — 3 个 Tool.

MCP (Model Context Protocol) server for AI Agent consumption.
Free tier: 100 calls/day.
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from astockevent.db.database import async_session_factory
from astockevent.db.models import Event, EventTimeline

logger = logging.getLogger(__name__)


async def check_events(
    stock_codes: str = "",
    event_types: str = "",
    since: str = "",
    limit: int = 50,
) -> list[dict]:
    """MCP Tool 1: 检查指定股票池的结构化公告事件."""
    async with async_session_factory() as db:
        query = select(Event).where(Event.status != "corrected")

        if stock_codes:
            codes = [c.strip().zfill(6) for c in stock_codes.split(",") if c.strip()]
            query = query.where(Event.stock_code.in_(codes))

        if event_types:
            types = [t.strip() for t in event_types.split(",") if t.strip()]
            query = query.where(Event.event_type.in_(types))

        if since:
            try:
                since_dt = datetime.fromisoformat(since)
                query = query.where(Event.last_updated_at >= since_dt)
            except ValueError:
                pass
        else:
            since_date = date.today() - timedelta(days=7)
            query = query.where(Event.last_updated_at >= datetime(since_date.year, since_date.month, since_date.day, tzinfo=timezone.utc))

        query = query.order_by(Event.last_updated_at.desc()).limit(min(limit, 200))
        result = await db.execute(query)
        rows = result.scalars().all()

        return [_event_to_mcp_dict(row) for row in rows]


async def get_event_timeline(event_id: str) -> dict | None:
    """MCP Tool 2: 获取单个事件的完整生命周期时间线."""
    from uuid import UUID

    try:
        uid = UUID(event_id)
    except ValueError:
        return None

    async with async_session_factory() as db:
        result = await db.execute(select(Event).where(Event.event_id == uid))
        event = result.scalar_one_or_none()
        if not event:
            return None

        tl_result = await db.execute(
            select(EventTimeline)
            .where(EventTimeline.event_id == uid)
            .order_by(EventTimeline.entry_date)
        )
        timelines = tl_result.scalars().all()

        return {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "stock_code": event.stock_code,
            "stock_name": event.stock_name,
            "status": event.status,
            "phase": event.phase,
            "structured_payload": event.structured_payload or {},
            "ai_summary": event.ai_summary or "",
            "confidence_tier": event.confidence_tier,
            "timeline": [
                {
                    "date": t.entry_date.isoformat(),
                    "phase": t.phase,
                    "description": t.description,
                }
                for t in timelines
            ],
            "related_events": [str(r) for r in (event.related_events or [])],
            "last_updated_at": event.last_updated_at.isoformat(),
        }


async def get_upcoming_events(
    stock_codes: str = "",
    days: int = 7,
    event_types: str = "",
) -> list[dict]:
    """MCP Tool 3: 获取未来 N 天内即将发生的事件."""
    today = date.today()
    future = today + timedelta(days=min(days, 30))

    async with async_session_factory() as db:
        conditions = [
            Event.status.in_(["active", "updating"]),
            Event.announcement_date >= today,
        ]

        if stock_codes:
            codes = [c.strip().zfill(6) for c in stock_codes.split(",") if c.strip()]
            conditions.append(Event.stock_code.in_(codes))

        if event_types:
            types = [t.strip() for t in event_types.split(",") if t.strip()]
            conditions.append(Event.event_type.in_(types))

        query = select(Event).where(and_(*conditions)).order_by(Event.announcement_date).limit(100)
        result = await db.execute(query)
        rows = result.scalars().all()

        events = []
        for row in rows:
            if row.announcement_date:
                remaining = (row.announcement_date - today).days
                if 0 <= remaining <= days:
                    events.append({
                        "event_id": str(row.event_id),
                        "event_type": row.event_type,
                        "stock_code": row.stock_code,
                        "stock_name": row.stock_name,
                        "due_date": row.announcement_date.isoformat(),
                        "days_remaining": remaining,
                        "ai_summary": row.ai_summary or "",
                    })

        return events


def _event_to_mcp_dict(event: Event) -> dict:
    return {
        "event_id": str(event.event_id),
        "event_type": event.event_type,
        "stock_code": event.stock_code,
        "stock_name": event.stock_name,
        "status": event.status,
        "phase": event.phase,
        "confidence_tier": event.confidence_tier,
        "ai_summary": event.ai_summary or "",
        "announcement_date": event.announcement_date.isoformat(),
        "last_updated_at": event.last_updated_at.isoformat(),
        "structured_payload": event.structured_payload or {},
    }


# ====== MCP stdio server (optional Phase 2) ======
# This module can be run as a standalone MCP server using the Python MCP SDK.
# For MVP, it's integrated into the FastAPI app as REST endpoints.
# The 3 tools above are callable from any MCP-compatible framework.
