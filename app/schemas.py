
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr
from enum import Enum


class Category(str, Enum):
    REFUND = "refund"
    BILLING = "billing"
    PAYMENT_FAILURE = "payment_failure"
    CANCELLATION = "cancellation"
    TECHNICAL_ISSUE = "technical_issue"
    ACCOUNT_ISSUE = "account_issue"
    FEATURE_REQUEST = "feature_request"
    GENERAL_QUESTION = "general_question"
    FRAUD = "fraud"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RefundDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    eligible: bool = False
    amount_inr: int = Field(default=0, ge=0)
    reason: str
    requires_human_review: bool = True


class TriageResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ticket_id: str
    category: Category
    severity: Severity
    refund: RefundDecision
    reply_draft: str
    needs_human: bool
    confidence: float = Field(ge=0.0, le=1.0)
    confidence_reason: str
    prompt_injection_detected: bool = False
    processing_mode: str = "rules"


class Purchase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr = Field(min_length=1)
    type: StrictStr = Field(min_length=1)
    amount_inr: StrictInt = Field(ge=0)
    status: StrictStr = Field(min_length=1)
    at: datetime


class TicketInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: StrictStr = Field(min_length=1, max_length=100)
    received_at: datetime
    subject: StrictStr = Field(min_length=1, max_length=500)
    body: StrictStr = Field(min_length=1, max_length=10000)
    purchases: list[Purchase] = Field(max_length=100)
    app_opens_since_renewal: StrictInt = Field(ge=0)
