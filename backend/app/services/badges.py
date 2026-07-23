"""Паттерн-бейдж детекциясы.

Табалдырықтар ТӘУЕЛСІЗ авторлармен саналады (1 автор = 1 дауыс), тек көрінетін
(жарияланған, жасырылмаған) контент есепке кіреді. Контент жасырылып табалдырықтан
түссе, бейдж қайтарылып алынады (revoked_at) - әділдік екі жаққа да.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CompanyBadge,
    DiscriminationDetail,
    Review,
    VacancyComplaint,
)

SALARY_THRESHOLD = 5
LANGUAGE_THRESHOLD = 3
FINES_THRESHOLD = 3

COMPLAINT_VISIBLE = (
    VacancyComplaint.moderation_status == "published",
    VacancyComplaint.hidden_at.is_(None),
    VacancyComplaint.deleted_at.is_(None),
)
REVIEW_VISIBLE = (
    Review.moderation_status == "published",
    Review.hidden_at.is_(None),
    Review.deleted_at.is_(None),
)


async def _salary_fraud_authors(db: AsyncSession, company_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(func.distinct(VacancyComplaint.author_id))).where(
                VacancyComplaint.company_id == company_id,
                VacancyComplaint.category == "salary_fraud",
                *COMPLAINT_VISIBLE,
            )
        )
        or 0
    )


async def _language_discrimination_authors(
    db: AsyncSession, company_id: uuid.UUID
) -> int:
    """Тіл-кемсіту блоктары отзывта да, шағымда да болуы мүмкін - екеуі бірге."""
    review_authors = (
        select(Review.author_id)
        .join(DiscriminationDetail, DiscriminationDetail.review_id == Review.id)
        .where(
            Review.company_id == company_id,
            DiscriminationDetail.kind == "language",
            *REVIEW_VISIBLE,
        )
    )
    complaint_authors = (
        select(VacancyComplaint.author_id)
        .join(
            DiscriminationDetail,
            DiscriminationDetail.complaint_id == VacancyComplaint.id,
        )
        .where(
            VacancyComplaint.company_id == company_id,
            DiscriminationDetail.kind == "language",
            *COMPLAINT_VISIBLE,
        )
    )
    combined = review_authors.union(complaint_authors).subquery()
    return await db.scalar(select(func.count()).select_from(combined)) or 0


async def _illegal_fines_authors(db: AsyncSession, company_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count(func.distinct(Review.author_id))).where(
                Review.company_id == company_id,
                Review.illegal_fines.is_(True),
                *REVIEW_VISIBLE,
            )
        )
        or 0
    )


async def recompute_badges(db: AsyncSession, company_id: uuid.UUID) -> None:
    """Компанияның үш паттерн-бейджін қайта есептеп, award/revoke жасайды.

    Коммитті ШАҚЫРУШЫ жасайды (өз транзакциясының ішінде қолданылады).
    """
    counts = {
        "salary_not_confirmed": (
            await _salary_fraud_authors(db, company_id),
            SALARY_THRESHOLD,
        ),
        "repeated_language_discrimination": (
            await _language_discrimination_authors(db, company_id),
            LANGUAGE_THRESHOLD,
        ),
        "repeated_illegal_fines": (
            await _illegal_fines_authors(db, company_id),
            FINES_THRESHOLD,
        ),
    }
    existing_rows = (
        await db.scalars(
            select(CompanyBadge).where(
                CompanyBadge.company_id == company_id,
                or_(*(CompanyBadge.badge == b for b in counts)),
            )
        )
    ).all()
    existing = {row.badge: row for row in existing_rows}

    for badge, (count, threshold) in counts.items():
        met = count >= threshold
        row = existing.get(badge)
        note = f"{count} тәуелсіз автор (табалдырық: {threshold})"
        if met and row is None:
            db.add(CompanyBadge(company_id=company_id, badge=badge, note=note))
        elif met and row is not None:
            row.note = note
            row.revoked_at = None
        elif not met and row is not None and row.revoked_at is None:
            row.note = note
            row.revoked_at = datetime.now(timezone.utc)
