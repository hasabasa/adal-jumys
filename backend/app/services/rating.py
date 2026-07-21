"""Жұмыс беруші рейтингі: салмақты Байес орташасы.

Формула және барлық константа docs/rating.md-де ашық документтелген.
Өзгертсең, ол файлды да жаңарт: ашық формула - сенім-ядро.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review

VERIFIED_WEIGHT = 1.0
UNVERIFIED_WEIGHT = 0.4
CONFIDENCE_M = 5.0
# Салмақ 2.5 жылда екі есе азаяды: ескі кейс компанияны мәңгі жазаламайды
HALF_LIFE_DAYS = 912.5
# Платформада отзыв аз кезде C осыған тартылады (1-10 шкаласының ортасы)
NEUTRAL_PRIOR = 5.5

VISIBLE = (
    Review.moderation_status == "published",
    Review.hidden_at.is_(None),
    Review.deleted_at.is_(None),
)


@dataclass
class EmployerRating:
    rating: float | None
    review_count: int
    verified_count: int


def _weight(verification_status: str, created_at: datetime) -> float:
    base = VERIFIED_WEIGHT if verification_status == "verified" else UNVERIFIED_WEIGHT
    age_days = (datetime.now(timezone.utc) - created_at).days
    return base * 0.5 ** (age_days / HALF_LIFE_DAYS)


async def global_mean(db: AsyncSession) -> float:
    scores = (await db.scalars(select(Review.overall_score).where(*VISIBLE))).all()
    if not scores:
        return NEUTRAL_PRIOR
    return sum(scores) / len(scores)


async def employer_rating(db: AsyncSession, company_id) -> EmployerRating:
    rows = (
        await db.execute(
            select(
                Review.overall_score, Review.verification_status, Review.created_at
            ).where(Review.company_id == company_id, *VISIBLE)
        )
    ).all()
    if not rows:
        return EmployerRating(rating=None, review_count=0, verified_count=0)

    mean = await global_mean(db)
    weighted_sum = 0.0
    weight_total = 0.0
    verified_count = 0
    for score, verification_status, created_at in rows:
        w = _weight(verification_status, created_at)
        weighted_sum += w * score
        weight_total += w
        if verification_status == "verified":
            verified_count += 1

    rating = (weighted_sum + CONFIDENCE_M * mean) / (weight_total + CONFIDENCE_M)
    return EmployerRating(
        rating=round(rating, 1),
        review_count=len(rows),
        verified_count=verified_count,
    )
