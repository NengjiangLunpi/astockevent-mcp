"""Pydantic models matching the API contract."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, Field


# ====== Enums ======

class EventType(str, Enum):
    share_reduction = "share_reduction"
    delisting_risk = "delisting_risk"
    regulatory_letter = "regulatory_letter"
    lockup_expiration = "lockup_expiration"
    share_buyback = "share_buyback"


class EventCategory(str, Enum):
    equity_change = "equity_change"
    regulatory = "regulatory"
    corporate_action = "corporate_action"
    delisting_risk = "delisting_risk"


class EventStatus(str, Enum):
    active = "active"
    updating = "updating"
    closed = "closed"
    corrected = "corrected"
    archived = "archived"


class ConfidenceTier(str, Enum):
    verified = "verified"
    likely = "likely"
    uncertain = "uncertain"


class Market(str, Enum):
    SH = "SH"
    SZ = "SZ"
    BJ = "BJ"


class AnnouncementTime(str, Enum):
    pre_market = "pre_market"
    midday = "midday"
    after_market = "after_market"
    weekend = "weekend"


# ====== Source ======

class PrimarySource(BaseModel):
    name: str
    url: str
    announcement_id: Optional[str] = None


class EventSource(BaseModel):
    primary: PrimarySource
    cross_validated: bool = False
    cross_sources: list[str] = Field(default_factory=list)


# ====== Timeline ======

class TimelineEntry(BaseModel):
    date: date
    phase: str
    description: str
    source_url: Optional[str] = None


# ====== Event ======

class EventSummary(BaseModel):
    """Event as returned in list endpoints."""
    event_id: str
    event_type: EventType
    stock_code: str
    stock_name: Optional[str] = None
    market: Market
    status: EventStatus
    phase: str
    confidence_tier: ConfidenceTier
    confidence_reasons: list[str] = Field(default_factory=list)
    quantitative_tags: dict = Field(default_factory=dict)
    ai_summary: str = ""
    announcement_date: date
    announcement_time: Optional[AnnouncementTime] = None
    last_updated_at: datetime
    source: EventSource
    source_url: Optional[str] = None

    model_config = {"from_attributes": True}


class EventDetail(EventSummary):
    """Event with full structured_payload + timeline."""
    structured_payload: dict = Field(default_factory=dict)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    related_events: list[str] = Field(default_factory=list)
    merge_parent: Optional[str] = None
    first_seen_at: datetime
    schema_version: str = "0.1.0"


# ====== API Error ======

class APIError(BaseModel):
    code: str
    message: str


# ====== API Response ======

class ResponseMeta(BaseModel):
    cursor: Optional[str] = None
    has_more: bool = False
    request_id: str


class EventListResponse(BaseModel):
    data: list[EventSummary]
    meta: ResponseMeta
    error: Optional[APIError] = None


class EventDetailResponse(BaseModel):
    data: EventDetail
    meta: ResponseMeta
    error: Optional[APIError] = None


# ====== Upcoming ======

class UpcomingEvent(BaseModel):
    event_id: str
    event_type: EventType
    stock_code: str
    stock_name: Optional[str] = None
    due_date: date
    days_remaining: int
    ai_summary: str = ""


class UpcomingResponse(BaseModel):
    data: list[UpcomingEvent]
    meta: ResponseMeta
    error: Optional[APIError] = None


class ErrorResponse(BaseModel):
    data: None = None
    meta: ResponseMeta
    error: APIError
