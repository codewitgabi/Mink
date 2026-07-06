from fastapi import APIRouter, Depends, Query

from api.response import success_response
from api.v1.dependencies.auth import get_current_user_id
from api.v1.schemas.user import HandleAvailabilityResponse, UpdateProfileRequest, UserResponse
from api.v1.services.user import user_service

router = APIRouter(tags=["Users"])


@router.get("/handles/{handle}/availability")
async def check_handle_availability(handle: str):
    available = await user_service.is_handle_available(handle)
    return success_response(
        "Handle availability checked",
        data=HandleAvailabilityResponse(
            handle=handle.lower(), available=available
        ).model_dump(),
    )


@router.get("/users/me")
async def get_my_profile(user_id: str = Depends(get_current_user_id)):
    user = await user_service.get_by_id(user_id)
    return success_response(
        "Profile fetched", data=UserResponse(**user.model_dump()).model_dump()
    )


@router.patch("/users/me")
async def update_my_profile(
    payload: UpdateProfileRequest, user_id: str = Depends(get_current_user_id)
):
    user = await user_service.update_profile(
        user_id, payload.model_dump(exclude_unset=True)
    )
    return success_response(
        "Profile updated", data=UserResponse(**user.model_dump()).model_dump()
    )


@router.get("/users/search")
async def search_users(
    q: str = Query(..., min_length=1), limit: int = Query(20, le=50)
):
    users = await user_service.search_users(q, limit)
    return success_response(
        "Search results",
        data={"results": [UserResponse(**u.model_dump()).model_dump() for u in users]},
    )


@router.get("/users/{handle}")
async def get_user_by_handle(handle: str):
    user = await user_service.get_by_handle(handle)
    return success_response(
        "User fetched", data=UserResponse(**user.model_dump()).model_dump()
    )
