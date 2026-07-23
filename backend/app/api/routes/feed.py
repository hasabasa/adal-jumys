from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.models import Company, Review, User, VacancyComplaint
from app.schemas.feed import FeedItem, PlatformStats

router = APIRouter(tags=["feed"])

REVIEW_VISIBLE = (
    Review.moderation_status == "published",
    Review.hidden_at.is_(None),
    Review.deleted_at.is_(None),
)
COMPLAINT_VISIBLE = (
    VacancyComplaint.moderation_status == "published",
    VacancyComplaint.hidden_at.is_(None),
    VacancyComplaint.deleted_at.is_(None),
)


@router.get("/feed", response_model=list[FeedItem])
async def feed(
    db: DbSession, limit: int = Query(default=20, ge=1, le=50)
) -> list[FeedItem]:
    """Соңғы жазбалар: отзыв + шағым аралас, жаңасы бірінші."""
    review_rows = await db.execute(
        select(Review, User.pseudonym, Company.name)
        .join(User, Review.author_id == User.id)
        .join(Company, Review.company_id == Company.id)
        .where(*REVIEW_VISIBLE, Company.hidden_at.is_(None))
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    complaint_rows = await db.execute(
        select(VacancyComplaint, User.pseudonym, Company.name)
        .join(User, VacancyComplaint.author_id == User.id)
        .join(Company, VacancyComplaint.company_id == Company.id)
        .where(*COMPLAINT_VISIBLE, Company.hidden_at.is_(None))
        .order_by(VacancyComplaint.created_at.desc())
        .limit(limit)
    )
    items: list[FeedItem] = []
    for review, pseudonym, company_name in review_rows.all():
        items.append(
            FeedItem(
                type="review",
                id=review.id,
                company_id=review.company_id,
                company_name=company_name,
                author_pseudonym=pseudonym,
                body=review.body,
                created_at=review.created_at,
                overall_score=review.overall_score,
                verification_status=review.verification_status,
            )
        )
    for complaint, pseudonym, company_name in complaint_rows.all():
        items.append(
            FeedItem(
                type="complaint",
                id=complaint.id,
                company_id=complaint.company_id,
                company_name=company_name,
                author_pseudonym=pseudonym,
                body=complaint.body,
                created_at=complaint.created_at,
                category=complaint.category,
                source_type=complaint.source_type,
                advertised_salary=complaint.advertised_salary,
                actual_salary=complaint.actual_salary,
            )
        )
    items.sort(key=lambda item: item.created_at, reverse=True)
    return items[:limit]


@router.get("/stats", response_model=PlatformStats)
async def stats(db: DbSession) -> PlatformStats:
    companies = await db.scalar(
        select(func.count()).select_from(Company).where(Company.hidden_at.is_(None))
    )
    reviews = await db.scalar(
        select(func.count()).select_from(Review).where(*REVIEW_VISIBLE)
    )
    complaints = await db.scalar(
        select(func.count())
        .select_from(VacancyComplaint)
        .where(*COMPLAINT_VISIBLE)
    )
    return PlatformStats(
        companies=companies or 0, reviews=reviews or 0, complaints=complaints or 0
    )
