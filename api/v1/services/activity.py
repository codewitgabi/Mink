from datetime import datetime, timezone
from typing import Optional

from api.database import db
from api.v1.models.activity import Activity


class ActivityService:
    """Business logic for indexed payment activity."""

    @property
    def _collection(self):
        return db.get_db()["activities"]

    async def record_payment(
        self,
        payer_id: str,
        payee_id: str,
        amount: float,
        currency: str,
        related_request_id: Optional[str] = None,
        tx_hash: Optional[str] = None,
    ) -> tuple[Activity, Activity]:
        """Write one activity row for each side of a completed payment."""
        now = datetime.now(timezone.utc)

        outgoing = Activity(
            user_id=payer_id,
            counterparty_id=payee_id,
            direction="outgoing",
            amount=amount,
            currency=currency,
            related_request_id=related_request_id,
            tx_hash=tx_hash,
            created_at=now,
        )
        incoming = Activity(
            user_id=payee_id,
            counterparty_id=payer_id,
            direction="incoming",
            amount=amount,
            currency=currency,
            related_request_id=related_request_id,
            tx_hash=tx_hash,
            created_at=now,
        )

        result = await self._collection.insert_many(
            [outgoing.model_dump(exclude={"id"}), incoming.model_dump(exclude={"id"})]
        )
        outgoing.id = str(result.inserted_ids[0])
        incoming.id = str(result.inserted_ids[1])
        return outgoing, incoming

    async def list_for_user(
        self,
        user_id: str,
        direction: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        search: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[Activity]:
        query: dict = {"user_id": user_id}
        if direction:
            query["direction"] = direction
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["created_at"] = date_filter
        if search:
            matches = (
                await db.get_db()["users"]
                .find({"$text": {"$search": search}}, {"_id": 1})
                .to_list(length=None)
            )
            query["counterparty_id"] = {"$in": [str(m["_id"]) for m in matches]}

        cursor = (
            self._collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        )
        return [Activity(**doc) async for doc in cursor]

    async def monthly_summary(self, user_id: str) -> list[dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "direction": "$direction",
                    },
                    "total": {"$sum": "$amount"},
                }
            },
        ]
        rows = await self._collection.aggregate(pipeline).to_list(length=None)

        summary: dict[tuple[int, int], dict] = {}
        for row in rows:
            key = (row["_id"]["year"], row["_id"]["month"])
            entry = summary.setdefault(
                key,
                {
                    "year": key[0],
                    "month": key[1],
                    "total_incoming": 0.0,
                    "total_outgoing": 0.0,
                },
            )
            if row["_id"]["direction"] == "incoming":
                entry["total_incoming"] = row["total"]
            else:
                entry["total_outgoing"] = row["total"]

        results = sorted(
            summary.values(), key=lambda e: (e["year"], e["month"]), reverse=True
        )
        for entry in results:
            entry["net"] = entry["total_incoming"] - entry["total_outgoing"]
        return results


activity_service = ActivityService()
