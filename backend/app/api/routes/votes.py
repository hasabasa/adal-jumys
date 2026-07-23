import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, VisibleCompany, rate_limit
from app.models import HelpfulVote, Review, User, VacancyComplaint

router = APIRouter(tags=["votes"])


class HelpfulState(BaseModel):
    count: int
    voted: bool


async def _toggle(
    db: DbSession,
    user: User,
    review_id: uuid.UUID | None = None,
    complaint_id: uuid.UUID | None = None,
) -> HelpfulState:
    if review_id is not None:
        column = HelpfulVote.review_id
        target_id = review_id
    else:
        column = HelpfulVote.complaint_id
        target_id = complaint_id
    existing = await db.scalar(
        select(HelpfulVote).where(column == target_id, HelpfulVote.user_id == user.id)
    )
    if existing is not None:
        await db.delete(existing)
    else:
        db.add(
            HelpfulVote(
                review_id=review_id, complaint_id=complaint_id, user_id=user.id
            )
        )
    await db.commit()
    count = await db.scalar(
        select(func.count()).select_from(HelpfulVote).where(column == target_id)
    )
    return HelpfulState(count=count or 0, voted=existing is None)


@router.post(
    "/companies/{company_id}/reviews/{review_id}/helpful",
    response_model=HelpfulState,
    dependencies=[rate_limit(60, 3600, "helpful")],
)
async def toggle_review_helpful(
    company: VisibleCompany,
    review_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> HelpfulState:
    review = await db.get(Review, review_id)
    if review is None or review.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост табылмады"
        )
    return await _toggle(db, user, review_id=review_id)


@router.post(
    "/companies/{company_id}/complaints/{complaint_id}/helpful",
    response_model=HelpfulState,
    dependencies=[rate_limit(60, 3600, "helpful")],
)
async def toggle_complaint_helpful(
    company: VisibleCompany,
    complaint_id: uuid.UUID,
    db: DbSession,
    user: CurrentUser,
) -> HelpfulState:
    complaint = await db.get(VacancyComplaint, complaint_id)
    if complaint is None or complaint.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост табылмады"
        )
    return await _toggle(db, user, complaint_id=complaint_id)
