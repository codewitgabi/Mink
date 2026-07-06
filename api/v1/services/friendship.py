from datetime import datetime, timezone

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from api.database import db
from api.v1.models.friendship import Friendship
from api.v1.models.user import User
from api.v1.services.notification import notification_service


class FriendshipService:
    """Business logic for friend relationships and contact suggestions."""

    @property
    def _collection(self):
        return db.get_db()["friendships"]

    @property
    def _users(self):
        return db.get_db()["users"]

    @property
    def _activities(self):
        return db.get_db()["activities"]

    def _pair_query(self, a: str, b: str) -> dict:
        return {
            "$or": [
                {"requester_id": a, "addressee_id": b},
                {"requester_id": b, "addressee_id": a},
            ]
        }

    async def send_request(self, requester_id: str, addressee_id: str) -> Friendship:
        if requester_id == addressee_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot friend yourself")

        existing = await self._collection.find_one(
            self._pair_query(requester_id, addressee_id)
        )
        if existing:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Friendship already exists or is pending"
            )

        friendship = Friendship(requester_id=requester_id, addressee_id=addressee_id)
        result = await self._collection.insert_one(
            friendship.model_dump(exclude={"id"})
        )
        friendship.id = str(result.inserted_id)
        return friendship

    async def _get_incoming_request(
        self, friendship_id: str, addressee_id: str
    ) -> None:
        doc = await self._collection.find_one(
            {
                "_id": ObjectId(friendship_id),
                "addressee_id": addressee_id,
                "status": "pending",
            }
        )
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Friend request not found")

    async def _set_status(self, friendship_id: str, new_status: str) -> Friendship:
        doc = await self._collection.find_one_and_update(
            {"_id": ObjectId(friendship_id)},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Friendship not found")
        return Friendship(**doc)

    async def accept(self, friendship_id: str, addressee_id: str) -> Friendship:
        await self._get_incoming_request(friendship_id, addressee_id)
        friendship = await self._set_status(friendship_id, "accepted")
        await notification_service.create(
            friendship.requester_id,
            "friend_joined",
            {"friendship_id": friendship.id, "friend_id": addressee_id},
        )
        return friendship

    async def decline(self, friendship_id: str, addressee_id: str) -> Friendship:
        await self._get_incoming_request(friendship_id, addressee_id)
        return await self._set_status(friendship_id, "declined")

    async def remove_friend(self, user_id: str, friend_id: str) -> None:
        result = await self._collection.delete_one(
            {**self._pair_query(user_id, friend_id), "status": "accepted"}
        )
        if result.deleted_count == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Friendship not found")

    async def list_friends(self, user_id: str) -> list[Friendship]:
        cursor = self._collection.find(
            {
                "status": "accepted",
                "$or": [{"requester_id": user_id}, {"addressee_id": user_id}],
            }
        )
        return [Friendship(**doc) async for doc in cursor]

    async def list_incoming_requests(self, user_id: str) -> list[Friendship]:
        cursor = self._collection.find({"addressee_id": user_id, "status": "pending"})
        return [Friendship(**doc) async for doc in cursor]

    async def suggested_friends(self, user_id: str, limit: int = 10) -> list[User]:
        related = await self._collection.find(
            {"$or": [{"requester_id": user_id}, {"addressee_id": user_id}]}
        ).to_list(length=None)

        excluded_ids = {user_id}
        for r in related:
            excluded_ids.add(r["requester_id"])
            excluded_ids.add(r["addressee_id"])

        cursor = self._users.find(
            {"_id": {"$nin": [ObjectId(i) for i in excluded_ids]}}
        ).limit(limit)
        return [User(**doc) async for doc in cursor]

    async def _top_contacts(
        self, user_id: str, sort_field: str, limit: int
    ) -> list[dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$counterparty_id",
                    "last_activity_at": {"$max": "$created_at"},
                    "payment_count": {"$sum": 1},
                }
            },
            {"$sort": {sort_field: -1}},
            {"$limit": limit},
        ]
        results = await self._activities.aggregate(pipeline).to_list(length=None)

        contacts = []
        for r in results:
            user = await self._users.find_one({"_id": ObjectId(r["_id"])})
            if user is None:
                continue
            contacts.append(
                {
                    "user_id": str(user["_id"]),
                    "handle": user["handle"],
                    "display_name": user["display_name"],
                    "avatar_url": user.get("avatar_url"),
                    "last_activity_at": r["last_activity_at"],
                    "payment_count": r["payment_count"],
                }
            )
        return contacts

    async def recent_contacts(self, user_id: str, limit: int = 10) -> list[dict]:
        return await self._top_contacts(user_id, "last_activity_at", limit)

    async def frequently_paid_contacts(
        self, user_id: str, limit: int = 10
    ) -> list[dict]:
        return await self._top_contacts(user_id, "payment_count", limit)


friendship_service = FriendshipService()
