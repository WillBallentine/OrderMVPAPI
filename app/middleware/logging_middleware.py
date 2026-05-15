import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.activity_log import ActivityLog


class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return response

        action = _infer_action(request.method, request.url.path)
        client_ip = _get_client_ip(request)

        db: Session = SessionLocal()
        try:
            entry = ActivityLog(
                action=action,
                resource_type=_infer_resource(request.url.path),
                resource_id=_infer_resource_id(request.url.path),
                request_path=str(request.url.path),
                request_method=request.method,
                client_ip=client_ip,
                response_status=response.status_code,
                details=f'{{"duration_ms": {duration_ms}}}',
            )
            db.add(entry)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return response


def _infer_action(method: str, path: str) -> str:
    if "extract" in path or "upload" in path:
        return "UPLOAD"
    return {
        "GET": "READ",
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }.get(method.upper(), method.upper())


def _infer_resource(path: str) -> str:
    if "orders" in path:
        return "order"
    if "documents" in path:
        return "document"
    return "unknown"


def _infer_resource_id(path: str) -> str | None:
    parts = path.strip("/").split("/")
    for i, part in enumerate(parts):
        if part in ("orders", "documents") and i + 1 < len(parts):
            candidate = parts[i + 1]
            if candidate.isdigit():
                return candidate
    return None


def _get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
