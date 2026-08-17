from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class BookingMode(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"
    RANDOM = "random"


class BookingStatus(str, Enum):
    NOT_DISCUSSED = "not_discussed"
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DECLINED = "declined"


class InterestLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOT_INTERESTED = "not_interested"
    UNKNOWN = "unknown"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SiteVisitDetails(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None


class FollowUp(BaseModel):
    needed: bool = False
    when: Optional[str] = None


class LeadSlots(BaseModel):
    configuration: Optional[str] = None
    budget: Optional[str] = None
    budget_fit: Optional[str] = None
    timeline: Optional[str] = None
    purpose: Optional[str] = None
    preferred_language: Optional[str] = None
    interest_level: InterestLevel = InterestLevel.UNKNOWN
    objections: list[str] = Field(default_factory=list)
    site_visit_status: BookingStatus = BookingStatus.NOT_DISCUSSED
    site_visit_details: SiteVisitDetails = Field(default_factory=SiteVisitDetails)
    follow_up: FollowUp = Field(default_factory=FollowUp)
    opt_out: bool = False
    escalated_to_human: bool = False
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


class BookingResult(BaseModel):
    attempted: bool = False
    success: bool = False
    status: BookingStatus = BookingStatus.NOT_DISCUSSED
    message: Optional[str] = None
    slot: Optional[str] = None


class Analytics(BaseModel):
    lead_summary: str = ""
    configuration: Optional[str] = None
    budget: Optional[str] = None
    budget_fit: Optional[str] = None
    interest_level: InterestLevel = InterestLevel.UNKNOWN
    timeline: Optional[str] = None
    language_preference: Optional[str] = None
    objections_raised: list[str] = Field(default_factory=list)
    site_visit_status: BookingStatus = BookingStatus.NOT_DISCUSSED
    site_visit_details: SiteVisitDetails = Field(default_factory=SiteVisitDetails)
    follow_up_required: bool = False
    follow_up_time: Optional[str] = None
    opt_out: bool = False
    escalated_to_human: bool = False
    conversation_outcome: str = "ongoing"
    confidence_notes: Optional[str] = None


class Session(BaseModel):
    id: str
    messages: list[Message] = Field(default_factory=list)
    slots: LeadSlots = Field(default_factory=LeadSlots)
    booking_mode: BookingMode = BookingMode.SUCCESS
    booking_result: Optional[BookingResult] = None
    analytics: Optional[Analytics] = None
    ended: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CreateSessionResponse(BaseModel):
    session_id: str
    greeting: str
    slots: LeadSlots


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    slots: LeadSlots
    booking: Optional[BookingResult] = None


class EndSessionResponse(BaseModel):
    session_id: str
    analytics: Analytics
    ended: bool = True


class BookingModeUpdate(BaseModel):
    mode: Literal["success", "fail", "random"]
