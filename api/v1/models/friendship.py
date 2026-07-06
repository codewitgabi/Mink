from datetime import datetime
from typing import Literal

from pydantic import Field

from api.v1.models.common import MongoModel, utcnow

FriendshipStatus = Literal["pending", "accepted", "declined"]


class Friendship(MongoModel):
    requester_id: str
    addressee_id: str
    status: FriendshipStatus = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
