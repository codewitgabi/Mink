from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from api.v1.models.common import MongoModel, utcnow

ActivityDirection = Literal["incoming", "outgoing"]


class Activity(MongoModel):
    user_id: str
    counterparty_id: str
    direction: ActivityDirection
    amount: float
    currency: str
    related_request_id: Optional[str] = None
    tx_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
