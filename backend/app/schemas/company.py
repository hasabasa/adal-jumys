import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.services.bin_check import is_valid_bin


class CompanyCreate(BaseModel):
    bin: str = Field(pattern=r"^\d{12}$")
    name: str = Field(min_length=2, max_length=300)
    city: str | None = Field(default=None, max_length=100)
    address: str | None = Field(default=None, max_length=500)
    two_gis_url: HttpUrl | None = None
    website: HttpUrl | None = None

    @field_validator("bin")
    @classmethod
    def bin_checksum(cls, v: str) -> str:
        if not is_valid_bin(v):
            raise ValueError("БСН жарамсыз (чексум сәйкес емес)")
        return v


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
    source: str
    created_at: datetime
