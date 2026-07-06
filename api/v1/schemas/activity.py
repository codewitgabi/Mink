from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api.v1.models.activity import ActivityDirection


class ActivityResponse(BaseModel):
    id: str
    user_id: str
    counterparty_id: str
    direction: ActivityDirection
    amount: float
    currency: str
    related_request_id: Optional[str] = None
    tx_hash: Optional[str] = None
    created_at: datetime


class MonthlySummaryEntry(BaseModel):
    year: int
    month: int
    total_incoming: float
    total_outgoing: float
    net: float
