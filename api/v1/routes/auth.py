from fastapi import APIRouter, Header

from api.response import success_response
from api.v1.schemas.auth import LogoutRequest, RefreshTokenRequest, TokenResponse
from api.v1.schemas.user import UserResponse
from api.v1.services.auth import auth_service
from api.v1.utils.config import config

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(authorization: str = Header(...)):
    user, access_token, refresh_token = await auth_service.login(authorization)
    return success_response(
        "Logged in",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse(**user.model_dump()),
        ).model_dump(),
    )


@router.post("/refresh")
async def refresh(payload: RefreshTokenRequest):
    access_token, refresh_token = await auth_service.refresh(payload.refresh_token)
    return success_response(
        "Token refreshed",
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    )


@router.post("/logout")
async def logout(payload: LogoutRequest):
    await auth_service.logout(payload.refresh_token)
    return success_response("Logged out")
