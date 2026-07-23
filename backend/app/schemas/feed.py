import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, computed_field


class FeedItem(BaseModel):
    """Басты бет лентасының бір жазбасы: отзыв немесе шағым."""

    type: Literal["review", "complaint"]
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    author_pseudonym: str
    body: str
    created_at: datetime
    # review болса
    overall_score: int | None = None
    verification_status: str | None = None
    # complaint болса
    category: str | None = None
    source_type: str | None = None
    advertised_salary: int | None = None
    actual_salary: int | None = None

    @computed_field
    def salary_diff_percent(self) -> int | None:
        if not self.advertised_salary or self.actual_salary is None:
            return None
        return round(
            (self.actual_salary - self.advertised_salary)
            / self.advertised_salary
            * 100
        )


class PlatformStats(BaseModel):
    companies: int
    reviews: int
    complaints: int
