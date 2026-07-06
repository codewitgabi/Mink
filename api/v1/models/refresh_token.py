from datetime import datetime
from typing import Optional

from pydantic import Field

from api.v1.models.common import MongoModel, utcnow


class RefreshToken(MongoModel):
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utcnow)
