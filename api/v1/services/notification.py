from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from api.database import db
from api.v1.models.notification import Notification, NotificationType


class NotificationService:
    """Business logic for user notifications."""

    @property
    def _collection(self):
        return db.get_db()["notifications"]

    async def create(
        self, user_id: str, type: NotificationType, payload: dict
    ) -> Notification:
        notification = Notification(user_id=user_id, type=type, payload=payload)
        result = await self._collection.insert_one(
            notification.model_dump(exclude={"id"})
        )
        notification.id = str(result.inserted_id)
        return notification

    async def list_for_user(
        self, user_id: str, unread_only: bool = False, limit: int = 50
    ) -> list[Notification]:
        query: dict = {"user_id": user_id}
        if unread_only:
            query["read_at"] = None
        cursor = self._collection.find(query).sort("created_at", -1).limit(limit)
        return [Notification(**doc) async for doc in cursor]

    async def mark_read(self, notification_id: str, user_id: str) -> Notification:
        doc = await self._collection.find_one_and_update(
            {"_id": ObjectId(notification_id), "user_id": user_id},
            {"$set": {"read_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
        return Notification(**doc)


notification_service = NotificationService()
