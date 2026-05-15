import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional
from ..database import get_db
from ..dependencies import require_auth
from ..models.user import User
from ..services.pdf_extractor import extract_patient_info
from ..config import get_settings

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF"


@router.post(
    "/extract",
    summary="Extract Patient Info from PDF",
    operation_id="extract_patient_info",
    status_code=status.HTTP_200_OK,
)
async def extract_from_document(
    file: UploadFile = File(..., description="PDF document to extract patient info from"),
    db: Session = Depends(get_db),
    _: Optional[User] = Depends(require_auth),
):
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Received: {file.content_type}",
        )

    file_bytes = await file.read()

    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.max_upload_size_mb}MB",
        )

    if not file_bytes.startswith(PDF_MAGIC_BYTES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File does not appear to be a valid PDF",
        )

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, extract_patient_info, file_bytes)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to extract patient information from the document",
        )

    return {
        "filename": file.filename,
        "extracted": result,
    }
