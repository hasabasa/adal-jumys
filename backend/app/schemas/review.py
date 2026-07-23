import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.discrimination import DiscriminationCreate, DiscriminationPublic
from app.schemas.evidence import EvidencePublic
from app.schemas.response import CompanyResponsePublic


class ReviewCreate(BaseModel):
    overall_score: int = Field(ge=1, le=10)
    score_salary_timeliness: int | None = Field(default=None, ge=1, le=10)
    score_pension: int | None = Field(default=None, ge=1, le=10)
    score_overtime: int | None = Field(default=None, ge=1, le=10)
    score_contract: int | None = Field(default=None, ge=1, le=10)
    # Минимум 50 таңба: факт-формат бір сөзді "жаман" деген бағадан қорғайды
    body: str = Field(min_length=50, max_length=10_000)
    illegal_fines: bool = False
    employment_start: date | None = None
    employment_end: date | None = None
    discrimination: list[DiscriminationCreate] = Field(
        default_factory=list, max_length=5
    )

    @model_validator(mode="after")
    def employment_period_valid(self) -> "ReviewCreate":
        if (
            self.employment_start is not None
            and self.employment_end is not None
            and self.employment_end < self.employment_start
        ):
            raise ValueError("Жұмыс кезеңінің соңы басынан ерте бола алмайды")
        return self


class ReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    author_pseudonym: str
    overall_score: int
    score_salary_timeliness: int | None
    score_pension: int | None
    score_overtime: int | None
    score_contract: int | None
    body: str
    illegal_fines: bool
    employment_start: date | None
    employment_end: date | None
    verification_status: str
    created_at: datetime
    company_response: CompanyResponsePublic | None = None
    discrimination: list[DiscriminationPublic] = []
    evidence: list[EvidencePublic] = []
