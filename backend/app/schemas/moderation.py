import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HideRequest(BaseModel):
    # Себеп жария аудит-логта көрінеді, сондықтан мазмұнды болуы міндетті
    reason: str = Field(min_length=10, max_length=1000)


class VerificationDecision(BaseModel):
    method: Literal["employment_contract", "bank_statement", "other"]
    reason: str = Field(min_length=10, max_length=1000)


class VerificationQueueItem(BaseModel):
    review_id: uuid.UUID
    evidence_id: uuid.UUID
    company_name: str
    author_pseudonym: str
    created_at: datetime


class ModerationActionPublic(BaseModel):
    id: uuid.UUID
    actor_pseudonym: str | None
    action: str
    target_type: str
    target_id: uuid.UUID
    reason: str
    created_at: datetime


class AppealCreate(BaseModel):
    body: str = Field(min_length=10, max_length=2000)


class AppealPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    action_id: uuid.UUID
    status: str
    body: str
    created_at: datetime


class OverturnStat(BaseModel):
    """Модератор-жауапкершілік метрикасы: шешімі жиі бұзылатын модератор
    рөлінен айырылады (жария көрсеткіш)."""

    moderator_pseudonym: str
    total_actions: int
    overturned: int
