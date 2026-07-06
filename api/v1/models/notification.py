from datetime import datetime
from typing import Literal, Optional

from pydantic import Field

from api.v1.models.common import MongoModel, utcnow

NotificationType = Literal[
    "payment_received",
    "payment_sent",
    "request_received",
    "request_accepted",
    "reminder",
    "friend_joined",
    "ai_reminder",
]


class Notification(MongoModel):
    user_id: str
    type: NotificationType
    payload: dict = Field(default_factory=dict)
    delivered_via: list[str] = Field(default_factory=lambda: ["in_app"])
    read_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
