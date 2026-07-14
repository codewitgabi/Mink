from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from api.v1.models.user import Wallet


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    handle: Optional[str] = None
    wallets: Optional[list[Wallet]] = None
    preferences: Optional[dict] = None
    notification_settings: Optional[dict] = None


class HandleAvailabilityResponse(BaseModel):
    handle: str
    available: bool


class UserResponse(BaseModel):
    id: str
    handle: Optional[str] = None
    display_name: str
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None
    login_provider: Optional[str] = None
    onboarding_completed: bool = False
    wallets: list[Wallet] = Field(default_factory=list)
    preferences: dict = Field(default_factory=dict)
    notification_settings: dict = Field(default_factory=dict)
