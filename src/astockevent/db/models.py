"""⚠️ STUB — SQLAlchemy ORM models (Event, EventTimeline).

完整实现仅在私有仓库 NengjiangLunpi/astockevent (PRIVATE) 中。

本 Stub 提供 MCP Server 所需模型字段的结构参考，
使用 Pydantic 近似替代 SQLAlchemy declarative base。
"""

from datetime import date, datetime
from uuid import UUID


class Event:
    """⚠️ STUB: A股公告结构化事件（SQLAlchemy Model）。

    完整实现位于私有仓库，此为结构参考 Stub。
    MCP server.py 通过 SQLAlchemy query 访问此模型的以下字段。
    """

    event_id: UUID
    event_type: str
    stock_code: str
    stock_name: str | None = None
    status: str = "active"
    phase: str = "plan"
    confidence_tier: str = "verified"
    ai_summary: str = ""
    announcement_date: date | None = None
    last_updated_at: datetime
    structured_payload: dict | None = None
    related_events: list[UUID] | None = None

    def __init__(self, **kwargs):
        """⚠️ STUB: 构造器仅供类型参考，不可实例化。"""
        raise NotImplementedError(
            "Database models are not available in the public subset. "
            "Full implementation is in the private repo: "
            "https://github.com/NengjiangLunpi/astockevent"
        )


class EventTimeline:
    """⚠️ STUB: 事件生命周期时间线条目（SQLAlchemy Model）。

    完整实现位于私有仓库，此为结构参考 Stub。
    """

    event_id: UUID
    entry_date: date
    phase: str
    description: str

    def __init__(self, **kwargs):
        """⚠️ STUB: 构造器仅供类型参考，不可实例化。"""
        raise NotImplementedError(
            "Database models are not available in the public subset. "
            "Full implementation is in the private repo: "
            "https://github.com/NengjiangLunpi/astockevent"
        )
