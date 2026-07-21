from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, VisibleCompany
from app.models import User, VacancyComplaint
from app.schemas.complaint import ComplaintCreate, ComplaintPublic, ComplaintStats

router = APIRouter(prefix="/companies/{company_id}/complaints", tags=["complaints"])

VISIBLE = (
    VacancyComplaint.moderation_status == "published",
    VacancyComplaint.hidden_at.is_(None),
    VacancyComplaint.deleted_at.is_(None),
)


def to_public(complaint: VacancyComplaint, pseudonym: str) -> ComplaintPublic:
    return ComplaintPublic(
        id=complaint.id,
        company_id=complaint.company_id,
        author_pseudonym=pseudonym,
        category=complaint.category,
        stage=complaint.stage,
        source_type=complaint.source_type,
        source_url=complaint.source_url,
        advertised_salary=complaint.advertised_salary,
        actual_salary=complaint.actual_salary,
        body=complaint.body,
        created_at=complaint.created_at,
    )


@router.post("", response_model=ComplaintPublic, status_code=status.HTTP_201_CREATED)
async def create_complaint(
    company: VisibleCompany, data: ComplaintCreate, db: DbSession, user: CurrentUser
) -> ComplaintPublic:
    if user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Шағымды тек жұмысшы-аккаунт қалдыра алады",
        )
    complaint = VacancyComplaint(
        company_id=company.id,
        author_id=user.id,
        moderation_status="published",
        **data.model_dump(),
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)
    return to_public(complaint, user.pseudonym)


@router.get("", response_model=list[ComplaintPublic])
async def list_complaints(
    company: VisibleCompany,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ComplaintPublic]:
    rows = await db.execute(
        select(VacancyComplaint, User.pseudonym)
        .join(User, VacancyComplaint.author_id == User.id)
        .where(VacancyComplaint.company_id == company.id, *VISIBLE)
        .order_by(VacancyComplaint.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [to_public(complaint, pseudonym) for complaint, pseudonym in rows.all()]


@router.get("/stats", response_model=ComplaintStats)
async def complaint_stats(company: VisibleCompany, db: DbSession) -> ComplaintStats:
    rows = await db.execute(
        select(VacancyComplaint.category, func.count())
        .where(VacancyComplaint.company_id == company.id, *VISIBLE)
        .group_by(VacancyComplaint.category)
    )
    by_category = {category: count for category, count in rows.all()}
    return ComplaintStats(total=sum(by_category.values()), by_category=by_category)
