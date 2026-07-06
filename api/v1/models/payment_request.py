from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from api.v1.models.common import MongoModel, utcnow

PaymentRequestStatus = Literal[
    "pending", "accepted", "rejected", "cancelled", "expired"
]


class PaymentRequest(MongoModel):
    requester_id: str
    payer_id: str
    amount: float
    currency: str
    note: Optional[str] = None
    status: PaymentRequestStatus = "pending"
    expires_at: Optional[datetime] = None
    reminder_sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
