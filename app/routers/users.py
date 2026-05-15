from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..dependencies import require_auth, require_admin
from ..models.user import User
from ..schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    operation_id="get_current_user",
)
def get_me(current_user: Optional[User] = Depends(require_auth)):
    if current_user is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="JWT required for this endpoint")
    return current_user


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List Users (Admin)",
    operation_id="list_users",
)
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.query(User).offset(skip).limit(min(limit, 500)).all()
