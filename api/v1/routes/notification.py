from fastapi import APIRouter, Depends, Query

from api.response import success_response
from api.v1.dependencies.auth import get_current_user_id
from api.v1.schemas.notification import NotificationResponse
from api.v1.services.notification import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(50, le=100),
    user_id: str = Depends(get_current_user_id),
):
    notifications = await notification_service.list_for_user(
        user_id, unread_only, limit
    )
    return success_response(
        "Notifications fetched",
        data={
            "results": [
                NotificationResponse(**n.model_dump()).model_dump()
                for n in notifications
            ]
        },
    )


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, user_id: str = Depends(get_current_user_id)
):
    notification = await notification_service.mark_read(notification_id, user_id)
    return success_response(
        "Notification marked as read",
        data=NotificationResponse(**notification.model_dump()).model_dump(),
    )
