import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

# Рұқсат етілген форматтар: скрин/фото, құжат, аудио, видео
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
    "audio/mpeg",
    "audio/ogg",
    "video/mp4",
}


class EvidencePublic(BaseModel):
    """Жарияда тек id мен түрі: файлдың өзі /evidence/{id} арқылы беріледі."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mime_type: str | None
    pii_masked: bool


class EvidenceModeratorItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    review_id: uuid.UUID | None
    complaint_id: uuid.UUID | None
    purpose: str
    mime_type: str | None
    size_bytes: int | None
    status: str
    created_at: datetime


class EvidenceDecision(BaseModel):
    reason: str
    pii_masked: bool = False
