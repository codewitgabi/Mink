from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status
from pymongo import ReturnDocument

from api.database import db
from api.v1.models.payment_request import PaymentRequest
from api.v1.services.activity import activity_service
from api.v1.services.notification import notification_service


class PaymentRequestService:
    """Business logic for offchain payment requests."""

    @property
    def _collection(self):
        return db.get_db()["payment_requests"]

    async def create(
        self,
        requester_id: str,
        payer_id: str,
        amount: float,
        currency: str,
        note: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> PaymentRequest:
        if requester_id == payer_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Cannot request a payment from yourself"
            )

        payment_request = PaymentRequest(
            requester_id=requester_id,
            payer_id=payer_id,
            amount=amount,
            currency=currency,
            note=note,
            expires_at=expires_at,
        )
        result = await self._collection.insert_one(
            payment_request.model_dump(exclude={"id"})
        )
        payment_request.id = str(result.inserted_id)

        await notification_service.create(
            payer_id,
            "request_received",
            {
                "payment_request_id": payment_request.id,
                "amount": amount,
                "currency": currency,
            },
        )
        return payment_request

    async def _get_pending(self, request_id: str) -> dict:
        doc = await self._collection.find_one(
            {"_id": ObjectId(request_id), "status": "pending"}
        )
        if doc is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Payment request not found or not pending"
            )
        return doc

    async def cancel(self, request_id: str, requester_id: str) -> PaymentRequest:
        doc = await self._get_pending(request_id)
        if doc["requester_id"] != requester_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the requester can cancel this request"
            )
        return await self._set_status(request_id, "cancelled")

    async def reject(self, request_id: str, payer_id: str) -> PaymentRequest:
        doc = await self._get_pending(request_id)
        if doc["payer_id"] != payer_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the payer can reject this request"
            )
        return await self._set_status(request_id, "rejected")

    async def accept(self, request_id: str, payer_id: str) -> PaymentRequest:
        doc = await self._get_pending(request_id)
        if doc["payer_id"] != payer_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the payer can accept this request"
            )

        payment_request = await self._set_status(request_id, "accepted")

        await activity_service.record_payment(
            payer_id=payment_request.payer_id,
            payee_id=payment_request.requester_id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            related_request_id=payment_request.id,
        )
        await notification_service.create(
            payment_request.requester_id,
            "request_accepted",
            {
                "payment_request_id": payment_request.id,
                "amount": payment_request.amount,
            },
        )
        return payment_request

    async def send_reminder(self, request_id: str, requester_id: str) -> PaymentRequest:
        doc = await self._get_pending(request_id)
        if doc["requester_id"] != requester_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, "Only the requester can send a reminder"
            )

        await notification_service.create(
            doc["payer_id"],
            "reminder",
            {
                "payment_request_id": request_id,
                "amount": doc["amount"],
                "currency": doc["currency"],
            },
        )
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(request_id)},
            {"$set": {"reminder_sent_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        return PaymentRequest(**result)

    async def _set_status(self, request_id: str, new_status: str) -> PaymentRequest:
        doc = await self._collection.find_one_and_update(
            {"_id": ObjectId(request_id)},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )
        return PaymentRequest(**doc)

    async def expire_due_requests(self) -> int:
        """
        Mark pending requests whose ``expires_at`` has passed as expired.

        Not yet wired to a scheduler — call manually or from a future cron job.
        """
        result = await self._collection.update_many(
            {
                "status": "pending",
                "expires_at": {"$ne": None, "$lt": datetime.now(timezone.utc)},
            },
            {"$set": {"status": "expired", "updated_at": datetime.now(timezone.utc)}},
        )
        return result.modified_count

    async def list_incoming(self, payer_id: str) -> list[PaymentRequest]:
        cursor = self._collection.find({"payer_id": payer_id}).sort("created_at", -1)
        return [PaymentRequest(**doc) async for doc in cursor]

    async def list_outgoing(self, requester_id: str) -> list[PaymentRequest]:
        cursor = self._collection.find({"requester_id": requester_id}).sort(
            "created_at", -1
        )
        return [PaymentRequest(**doc) async for doc in cursor]


payment_request_service = PaymentRequestService()
