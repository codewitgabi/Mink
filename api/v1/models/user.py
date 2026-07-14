from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from api.v1.models.common import MongoModel, utcnow


class Wallet(BaseModel):
    chain: str
    address: str
    is_primary: bool = False


class User(MongoModel):
    handle: Optional[str] = None
    display_name: str
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None
    login_provider: Optional[str] = None
    magic_issuer: Optional[str] = None
    onboarding_completed: bool = False
    wallets: list[Wallet] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    notification_settings: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
