from fastapi import APIRouter

from api.v1.routes.activity import router as activity_router
from api.v1.routes.friendship import router as friendship_router
from api.v1.routes.notification import router as notification_router
from api.v1.routes.payment_request import router as payment_request_router
from api.v1.routes.user import router as user_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(user_router)
v1_router.include_router(friendship_router)
v1_router.include_router(payment_request_router)
v1_router.include_router(activity_router)
v1_router.include_router(notification_router)
