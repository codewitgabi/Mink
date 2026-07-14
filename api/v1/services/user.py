import re
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from api.database import db
from api.v1.models.user import User

HANDLE_RE = re.compile(r"^[a-z0-9_]{3,20}$")


class UserService:
    """Business logic for user identity: handles, profiles, search."""

    @property
    def _collection(self):
        return db.get_db()["users"]

    def _normalize_handle(self, handle: str) -> str:
        handle = handle.strip().lower()
        if not HANDLE_RE.match(handle):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Handles must be 3-20 characters: lowercase letters, numbers, underscores",
            )
        return handle

    async def is_handle_available(self, handle: str) -> bool:
        handle = self._normalize_handle(handle)
        existing = await self._collection.find_one({"handle": handle})
        return existing is None

    async def get_or_create_by_magic_issuer(self, magic_issuer: str, email: str) -> User:
        doc = await self._collection.find_one({"magic_issuer": magic_issuer})
        if doc is not None:
            if doc.get("email") != email:
                doc = await self._collection.find_one_and_update(
                    {"_id": doc["_id"]},
                    {"$set": {"email": email, "updated_at": datetime.now(timezone.utc)}},
                    return_document=ReturnDocument.AFTER,
                )
            return User(**doc)

        user = User(
            magic_issuer=magic_issuer,
            email=email,
            display_name=email.split("@")[0],
            login_provider="magic_link",
        )
        result = await self._collection.insert_one(
            user.model_dump(exclude={"id"}, exclude_none=True)
        )
        user.id = str(result.inserted_id)
        return user

    async def get_by_id(self, user_id: str) -> User:
        doc = await self._collection.find_one({"_id": ObjectId(user_id)})
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return User(**doc)

    async def get_by_handle(self, handle: str) -> User:
        doc = await self._collection.find_one({"handle": handle.strip().lower()})
        if doc is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return User(**doc)

    async def update_profile(self, user_id: str, updates: dict) -> User:
        updates = {k: v for k, v in updates.items() if v is not None}
        if "handle" in updates:
            updates["handle"] = self._normalize_handle(updates["handle"])
        if "wallets" in updates:
            updates["wallets"] = [
                w.model_dump() if hasattr(w, "model_dump") else w
                for w in updates["wallets"]
            ]
        updates["updated_at"] = datetime.now(timezone.utc)

        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return User(**result)

    async def complete_onboarding(self, user_id: str) -> User:
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {
                "$set": {
                    "onboarding_completed": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if result is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
        return User(**result)

    async def search_users(self, query: str, limit: int = 20) -> list[User]:
        cursor = self._collection.find({"$text": {"$search": query}}).limit(limit)
        return [User(**doc) async for doc in cursor]


user_service = UserService()
