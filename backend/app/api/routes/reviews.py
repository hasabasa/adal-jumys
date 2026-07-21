from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, VisibleCompany
from app.models import Review, User
from app.schemas.review import ReviewCreate, ReviewPublic

router = APIRouter(prefix="/companies/{company_id}/reviews", tags=["reviews"])


def to_public(review: Review, pseudonym: str) -> ReviewPublic:
    return ReviewPublic(
        id=review.id,
        company_id=review.company_id,
        author_pseudonym=pseudonym,
        overall_score=review.overall_score,
        score_salary_timeliness=review.score_salary_timeliness,
        score_pension=review.score_pension,
        score_overtime=review.score_overtime,
        score_contract=review.score_contract,
        body=review.body,
        employment_start=review.employment_start,
        employment_end=review.employment_end,
        verification_status=review.verification_status,
        created_at=review.created_at,
    )


@router.post("", response_model=ReviewPublic, status_code=status.HTTP_201_CREATED)
async def create_review(
    company: VisibleCompany, data: ReviewCreate, db: DbSession, user: CurrentUser
) -> ReviewPublic:
    if user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Отзывты тек жұмысшы-аккаунт қалдыра алады",
        )
    duplicate = await db.scalar(
        select(Review).where(
            Review.company_id == company.id, Review.author_id == user.id
        )
    )
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл компанияға отзывыңыз бар (1 компанияға 1 отзыв)",
        )
    review = Review(
        company_id=company.id,
        author_id=user.id,
        moderation_status="published",
        **data.model_dump(),
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return to_public(review, user.pseudonym)


@router.get("", response_model=list[ReviewPublic])
async def list_reviews(
    company: VisibleCompany,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewPublic]:
    rows = await db.execute(
        select(Review, User.pseudonym)
        .join(User, Review.author_id == User.id)
        .where(
            Review.company_id == company.id,
            Review.moderation_status == "published",
            Review.hidden_at.is_(None),
            Review.deleted_at.is_(None),
        )
        .order_by(Review.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [to_public(review, pseudonym) for review, pseudonym in rows.all()]
