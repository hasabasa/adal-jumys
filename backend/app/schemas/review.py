import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.review import REVIEW_PROBLEMS
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
    # docs/categories.md чеклисті (ЕК-баптарына байланған 13 категория)
    problems: list[str] = Field(default_factory=list, max_length=13)
    employment_start: date | None = None
    employment_end: date | None = None
    discrimination: list[DiscriminationCreate] = Field(
        default_factory=list, max_length=5
    )

    @field_validator("problems")
    @classmethod
    def problems_valid(cls, values: list[str]) -> list[str]:
        unknown = set(values) - set(REVIEW_PROBLEMS)
        if unknown:
            raise ValueError(f"Белгісіз категория: {', '.join(sorted(unknown))}")
        return list(dict.fromkeys(values))

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
    problems: list[str] = []
    employment_start: date | None
    employment_end: date | None
    verification_status: str
    created_at: datetime
    company_response: CompanyResponsePublic | None = None
    discrimination: list[DiscriminationPublic] = []
    evidence: list[EvidencePublic] = []
