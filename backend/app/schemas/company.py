import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.services.bin_check import is_valid_bin


class CompanyCreate(BaseModel):
    bin: str = Field(pattern=r"^\d{12}$")
    name: str = Field(min_length=2, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    two_gis_url: HttpUrl | None = None
    website: HttpUrl | None = None
    instagram_url: HttpUrl | None = None

    @field_validator("bin")
    @classmethod
    def bin_checksum(cls, v: str) -> str:
        if not is_valid_bin(v):
            raise ValueError("БСН жарамсыз (чексум сәйкес емес)")
        return v


class RepresentativeRequest(BaseModel):
    proof_method: Literal["domain_email", "official_letter", "other"]


class RepresentativePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    status: str
    proof_method: str | None
    created_at: datetime


class RepresentativeQueueItem(BaseModel):
    """Модератор кезегіне: кім, қай компанияға, қалай растамақ."""

    id: uuid.UUID
    company_name: str
    user_pseudonym: str
    proof_method: str | None
    status: str
    created_at: datetime


class BadgePublic(BaseModel):
    """Паттерн-бейдж: методологиясы docs/rating.md-де ашық."""

    model_config = ConfigDict(from_attributes=True)

    badge: str
    note: str | None
    awarded_at: datetime


class EmployerRatingPublic(BaseModel):
    """Жұмыс беруші осі. rating=None: отзыв әлі жоқ.

    Формула ашық: docs/rating.md
    """

    model_config = ConfigDict(from_attributes=True)

    rating: float | None
    review_count: int
    verified_count: int


class CompanyPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bin: str
    name: str
    legal_name: str | None
    city: str | None
    address: str | None
    oked: str | None
    two_gis_url: str | None
    website: str | None
    instagram_url: str | None
    source: str
    created_at: datetime
