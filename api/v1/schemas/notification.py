from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api.v1.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    payload: dict
    delivered_via: list[str]
    read_at: Optional[datetime] = None
    created_at: datetime
