from fastapi import APIRouter, Depends, Query, status

from api.response import success_response
from api.v1.dependencies.auth import get_current_user_id
from api.v1.schemas.friendship import (
    ContactSummary,
    FriendshipResponse,
    SendFriendRequest,
)
from api.v1.schemas.user import UserResponse
from api.v1.services.friendship import friendship_service

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def send_friend_request(
    payload: SendFriendRequest, user_id: str = Depends(get_current_user_id)
):
    friendship = await friendship_service.send_request(user_id, payload.addressee_id)
    return success_response(
        "Friend request sent",
        status_code=status.HTTP_201_CREATED,
        data=FriendshipResponse(**friendship.model_dump()).model_dump(),
    )


@router.post("/requests/{friendship_id}/accept")
async def accept_friend_request(
    friendship_id: str, user_id: str = Depends(get_current_user_id)
):
    friendship = await friendship_service.accept(friendship_id, user_id)
    return success_response(
        "Friend request accepted",
        data=FriendshipResponse(**friendship.model_dump()).model_dump(),
    )


@router.post("/requests/{friendship_id}/decline")
async def decline_friend_request(
    friendship_id: str, user_id: str = Depends(get_current_user_id)
):
    friendship = await friendship_service.decline(friendship_id, user_id)
    return success_response(
        "Friend request declined",
        data=FriendshipResponse(**friendship.model_dump()).model_dump(),
    )


@router.get("/requests/incoming")
async def list_incoming_requests(user_id: str = Depends(get_current_user_id)):
    requests = await friendship_service.list_incoming_requests(user_id)
    return success_response(
        "Incoming friend requests",
        data={
            "results": [
                FriendshipResponse(**r.model_dump()).model_dump() for r in requests
            ]
        },
    )


@router.get("/suggested")
async def suggested_friends(
    limit: int = Query(10, le=50), user_id: str = Depends(get_current_user_id)
):
    users = await friendship_service.suggested_friends(user_id, limit)
    return success_response(
        "Suggested friends",
        data={"results": [UserResponse(**u.model_dump()).model_dump() for u in users]},
    )


@router.get("/contacts/recent")
async def recent_contacts(
    limit: int = Query(10, le=50), user_id: str = Depends(get_current_user_id)
):
    contacts = await friendship_service.recent_contacts(user_id, limit)
    return success_response(
        "Recent contacts",
        data={"results": [ContactSummary(**c).model_dump() for c in contacts]},
    )


@router.get("/contacts/frequent")
async def frequent_contacts(
    limit: int = Query(10, le=50), user_id: str = Depends(get_current_user_id)
):
    contacts = await friendship_service.frequently_paid_contacts(user_id, limit)
    return success_response(
        "Frequently paid contacts",
        data={"results": [ContactSummary(**c).model_dump() for c in contacts]},
    )


@router.get("")
async def list_friends(user_id: str = Depends(get_current_user_id)):
    friends = await friendship_service.list_friends(user_id)
    return success_response(
        "Friends fetched",
        data={
            "results": [
                FriendshipResponse(**f.model_dump()).model_dump() for f in friends
            ]
        },
    )


@router.delete("/{friend_id}")
async def remove_friend(friend_id: str, user_id: str = Depends(get_current_user_id)):
    await friendship_service.remove_friend(user_id, friend_id)
    return success_response("Friend removed")
