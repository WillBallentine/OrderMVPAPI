from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..dependencies import require_api_key
from ..models.activity_log import ActivityLog
from ..schemas.activity_log import ActivityLogResponse

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get(
    "/",
    response_model=List[ActivityLogResponse],
    summary="List Activity Logs",
    operation_id="list_activity_logs",
)
def list_activity_logs(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: str = Depends(require_api_key),
):
    return (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
