from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from api.v1.models.friendship import FriendshipStatus


class SendFriendRequest(BaseModel):
    addressee_id: str


class FriendshipResponse(BaseModel):
    id: str
    requester_id: str
    addressee_id: str
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime


class ContactSummary(BaseModel):
    user_id: str
    handle: str
    display_name: str
    avatar_url: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    payment_count: Optional[int] = None
