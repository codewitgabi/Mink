from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.response import success_response
from api.v1.dependencies.auth import get_current_user_id
from api.v1.schemas.activity import ActivityResponse, MonthlySummaryEntry
from api.v1.services.activity import activity_service

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("")
async def list_activity(
    direction: Optional[str] = Query(default=None, pattern="^(incoming|outgoing)$"),
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(50, le=100),
    skip: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    activities = await activity_service.list_for_user(
        user_id,
        direction=direction,
        start_date=start_date,
        end_date=end_date,
        search=search,
        limit=limit,
        skip=skip,
    )
    return success_response(
        "Activity fetched",
        data={
            "results": [
                ActivityResponse(**a.model_dump()).model_dump() for a in activities
            ]
        },
    )


@router.get("/summary")
async def activity_summary(user_id: str = Depends(get_current_user_id)):
    summary = await activity_service.monthly_summary(user_id)
    return success_response(
        "Monthly summary",
        data={"results": [MonthlySummaryEntry(**s).model_dump() for s in summary]},
    )
