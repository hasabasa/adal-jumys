import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class HideRequest(BaseModel):
    # Себеп жария аудит-логта көрінеді, сондықтан мазмұнды болуы міндетті
    reason: str = Field(min_length=10, max_length=1000)


class ModerationActionPublic(BaseModel):
    id: uuid.UUID
    actor_pseudonym: str | None
    action: str
    target_type: str
    target_id: uuid.UUID
    reason: str
    created_at: datetime
