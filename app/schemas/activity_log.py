from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ActivityLogResponse(BaseModel):
    id: int
    action: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    request_path: str
    request_method: str
    client_ip: Optional[str]
    response_status: Optional[int]
    details: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
