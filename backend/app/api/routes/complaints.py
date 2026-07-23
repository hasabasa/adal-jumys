import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import and_, func, select

from app.api.deps import (
    CurrentUser,
    DbSession,
    VisibleCompany,
    require_approved_representative,
)
from app.models import CompanyResponse, User, VacancyComplaint
from app.schemas.complaint import ComplaintCreate, ComplaintPublic, ComplaintStats
from app.schemas.response import CompanyResponsePublic, ResponseCreate

router = APIRouter(prefix="/companies/{company_id}/complaints", tags=["complaints"])

VISIBLE = (
    VacancyComplaint.moderation_status == "published",
    VacancyComplaint.hidden_at.is_(None),
    VacancyComplaint.deleted_at.is_(None),
)


def to_public(
    complaint: VacancyComplaint, pseudonym: str, response: CompanyResponse | None = None
) -> ComplaintPublic:
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
        company_response=(
            CompanyResponsePublic.model_validate(response) if response else None
        ),
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
        select(VacancyComplaint, User.pseudonym, CompanyResponse)
        .join(User, VacancyComplaint.author_id == User.id)
        .outerjoin(
            CompanyResponse,
            and_(
                CompanyResponse.complaint_id == VacancyComplaint.id,
                CompanyResponse.moderation_status == "published",
            ),
        )
        .where(VacancyComplaint.company_id == company.id, *VISIBLE)
        .order_by(VacancyComplaint.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        to_public(complaint, pseudonym, response)
        for complaint, pseudonym, response in rows.all()
    ]


@router.post(
    "/{complaint_id}/response",
    response_model=CompanyResponsePublic,
    status_code=status.HTTP_201_CREATED,
)
async def respond_to_complaint(
    company: VisibleCompany,
    complaint_id: uuid.UUID,
    data: ResponseCreate,
    db: DbSession,
    user: CurrentUser,
) -> CompanyResponse:
    await require_approved_representative(db, company.id, user)
    complaint = await db.get(VacancyComplaint, complaint_id)
    if complaint is None or complaint.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Шағым табылмады"
        )
    existing = await db.scalar(
        select(CompanyResponse).where(CompanyResponse.complaint_id == complaint_id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл шағымға жауап берілген",
        )
    response = CompanyResponse(
        company_id=company.id,
        author_id=user.id,
        complaint_id=complaint_id,
        body=data.body,
        moderation_status="published",
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response


@router.get("/stats", response_model=ComplaintStats)
async def complaint_stats(company: VisibleCompany, db: DbSession) -> ComplaintStats:
    rows = await db.execute(
        select(VacancyComplaint.category, func.count())
        .where(VacancyComplaint.company_id == company.id, *VISIBLE)
        .group_by(VacancyComplaint.category)
    )
    by_category = {category: count for category, count in rows.all()}
    return ComplaintStats(total=sum(by_category.values()), by_category=by_category)
