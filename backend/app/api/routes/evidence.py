import uuid

from fastapi import APIRouter, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse, Response

from app.api.deps import DbSession
from app.core.config import get_settings
from app.models import EvidenceFile
from app.schemas.evidence import ALLOWED_MIME_TYPES
from app.services.storage import LocalStorage, get_storage

router = APIRouter(prefix="/evidence", tags=["evidence"])


async def store_upload(
    db: DbSession,
    file: UploadFile,
    *,
    review_id: uuid.UUID | None = None,
    complaint_id: uuid.UUID | None = None,
    report_id: uuid.UUID | None = None,
    purpose: str = "public_evidence",
) -> EvidenceFile:
    settings = get_settings()
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Файл тым үлкен (максимум {settings.max_upload_mb} МБ)",
        )
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Формат қабылданбайды (jpeg/png/webp/pdf/mp3/ogg/mp4 ғана)",
        )
    key = f"evidence/{uuid.uuid4()}"
    evidence = EvidenceFile(
        review_id=review_id,
        complaint_id=complaint_id,
        report_id=report_id,
        purpose=purpose,
        s3_key=key,
        mime_type=file.content_type,
        size_bytes=len(data),
        # Автор шешімі (24.07.2026): пре-модерация ЖОҚ - бірден жария,
        # шағым түскенде ғана тексеріліп жасырылады (реактив-модель)
        status="visible" if purpose == "public_evidence" else "pending_moderation",
    )
    await get_storage().save(key, data, file.content_type)
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


def serve_file(evidence: EvidenceFile) -> Response:
    storage = get_storage()
    if isinstance(storage, LocalStorage):
        return FileResponse(
            storage.path_for(evidence.s3_key), media_type=evidence.mime_type
        )
    return RedirectResponse(storage.presigned_url(evidence.s3_key))


@router.get("/{evidence_id}")
async def get_evidence_file(evidence_id: uuid.UUID, db: DbSession) -> Response:
    """Жария файл-беру: ТЕК модерациядан өткен (visible) дәлелдер."""
    evidence = await db.get(EvidenceFile, evidence_id)
    if evidence is None or evidence.status != "visible":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Дәлел табылмады"
        )
    return serve_file(evidence)
