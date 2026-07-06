from fastapi import APIRouter, Depends, status

from api.response import success_response
from api.v1.dependencies.auth import get_current_user_id
from api.v1.schemas.payment_request import CreatePaymentRequest, PaymentRequestResponse
from api.v1.services.payment_request import payment_request_service

router = APIRouter(prefix="/payment-requests", tags=["Payment Requests"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_payment_request(
    payload: CreatePaymentRequest, user_id: str = Depends(get_current_user_id)
):
    payment_request = await payment_request_service.create(
        requester_id=user_id,
        payer_id=payload.payer_id,
        amount=payload.amount,
        currency=payload.currency,
        note=payload.note,
        expires_at=payload.expires_at,
    )
    return success_response(
        "Payment request created",
        status_code=status.HTTP_201_CREATED,
        data=PaymentRequestResponse(**payment_request.model_dump()).model_dump(),
    )


@router.get("/incoming")
async def list_incoming_payment_requests(user_id: str = Depends(get_current_user_id)):
    requests = await payment_request_service.list_incoming(user_id)
    return success_response(
        "Incoming payment requests",
        data={
            "results": [
                PaymentRequestResponse(**r.model_dump()).model_dump() for r in requests
            ]
        },
    )


@router.get("/outgoing")
async def list_outgoing_payment_requests(user_id: str = Depends(get_current_user_id)):
    requests = await payment_request_service.list_outgoing(user_id)
    return success_response(
        "Outgoing payment requests",
        data={
            "results": [
                PaymentRequestResponse(**r.model_dump()).model_dump() for r in requests
            ]
        },
    )


@router.post("/{request_id}/accept")
async def accept_payment_request(
    request_id: str, user_id: str = Depends(get_current_user_id)
):
    payment_request = await payment_request_service.accept(request_id, user_id)
    return success_response(
        "Payment request accepted",
        data=PaymentRequestResponse(**payment_request.model_dump()).model_dump(),
    )


@router.post("/{request_id}/reject")
async def reject_payment_request(
    request_id: str, user_id: str = Depends(get_current_user_id)
):
    payment_request = await payment_request_service.reject(request_id, user_id)
    return success_response(
        "Payment request rejected",
        data=PaymentRequestResponse(**payment_request.model_dump()).model_dump(),
    )


@router.post("/{request_id}/cancel")
async def cancel_payment_request(
    request_id: str, user_id: str = Depends(get_current_user_id)
):
    payment_request = await payment_request_service.cancel(request_id, user_id)
    return success_response(
        "Payment request cancelled",
        data=PaymentRequestResponse(**payment_request.model_dump()).model_dump(),
    )


@router.post("/{request_id}/remind")
async def remind_payment_request(
    request_id: str, user_id: str = Depends(get_current_user_id)
):
    payment_request = await payment_request_service.send_reminder(request_id, user_id)
    return success_response(
        "Reminder sent",
        data=PaymentRequestResponse(**payment_request.model_dump()).model_dump(),
    )
