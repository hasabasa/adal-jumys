import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

Category = Literal[
    "salary_fraud",
    "fake_vacancy",
    "paid_training",
    "unethical_questions",
    "rudeness",
    "ghost_vacancy",
    "unpaid_test_task",
    "discrimination",
]
Stage = Literal["announcement", "call", "interview", "offer"]
SourceType = Literal["hh", "olx", "instagram", "threads", "telegram", "whatsapp", "other"]


class ComplaintCreate(BaseModel):
    category: Category
    stage: Stage
    source_type: SourceType
    source_url: str | None = Field(default=None, max_length=1000)
    advertised_salary: int | None = Field(default=None, ge=0)
    actual_salary: int | None = Field(default=None, ge=0)
    body: str = Field(min_length=50, max_length=10_000)

    @model_validator(mode="after")
    def salary_pair_required_for_fraud(self) -> "ComplaintCreate":
        if self.category == "salary_fraud" and (
            self.advertised_salary is None or self.actual_salary is None
        ):
            raise ValueError(
                "salary_fraud шағымына жарияланған және нақты жалақы міндетті"
            )
        return self


class ComplaintPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    author_pseudonym: str
    category: str
    stage: str
    source_type: str
    source_url: str | None
    advertised_salary: int | None
    actual_salary: int | None
    body: str
    created_at: datetime

    @computed_field
    def salary_diff_percent(self) -> int | None:
        """Жарияланған мен нақты жалақы айырмасы: жүйе өзі есептеп көрсетеді."""
        if not self.advertised_salary or self.actual_salary is None:
            return None
        return round(
            (self.actual_salary - self.advertised_salary) / self.advertised_salary * 100
        )


class ComplaintStats(BaseModel):
    """Жалдаушы осі: сан-рейтинг емес, ашық статистика."""

    total: int
    by_category: dict[str, int]
