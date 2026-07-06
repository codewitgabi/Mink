from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from api.v1.models.payment_request import PaymentRequestStatus


class CreatePaymentRequest(BaseModel):
    payer_id: str
    amount: float = Field(gt=0)
    currency: str
    note: Optional[str] = None
    expires_at: Optional[datetime] = None


class PaymentRequestResponse(BaseModel):
    id: str
    requester_id: str
    payer_id: str
    amount: float
    currency: str
    note: Optional[str] = None
    status: PaymentRequestStatus
    expires_at: Optional[datetime] = None
    reminder_sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
