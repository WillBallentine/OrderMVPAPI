from fastapi import Security, Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from .config import get_settings
from .database import get_db
from .models.user import User, Role
from .services.auth_service import decode_token

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

_AUTH_REQUIRED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or missing credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def require_auth(
    token: Optional[str] = Depends(oauth2_scheme),
    api_key: Optional[str] = Security(API_KEY_HEADER),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Accept either a JWT bearer token or the service API key."""
    settings = get_settings()

    if token:
        username = decode_token(token)
        if not username:
            raise _AUTH_REQUIRED
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user:
            raise _AUTH_REQUIRED
        return user

    if api_key and api_key == settings.api_key:
        return None

    raise _AUTH_REQUIRED


async def require_admin(current_user: Optional[User] = Depends(require_auth)) -> User:
    if current_user is None or current_user.role != Role.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return current_user
