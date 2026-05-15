import json
from sqlalchemy.orm import Session
from ..models.activity_log import ActivityLog


def log_activity(
    db: Session,
    action: str,
    request_path: str,
    request_method: str,
    resource_type: str = None,
    resource_id: str = None,
    client_ip: str = None,
    response_status: int = None,
    details: dict = None,
) -> None:
    entry = ActivityLog(
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        request_path=request_path,
        request_method=request_method,
        client_ip=client_ip,
        response_status=response_status,
        details=json.dumps(details) if details else None,
    )
    db.add(entry)
    db.commit()
