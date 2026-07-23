import uuid

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, func, select

from app.api.deps import (
    CurrentUser,
    DbSession,
    VisibleCompany,
    rate_limit,
    require_approved_representative,
)
from app.api.routes.evidence import store_upload
from app.models import (
    CompanyResponse,
    DiscriminationDetail,
    EvidenceFile,
    HelpfulVote,
    User,
    VacancyComplaint,
)
from app.schemas.complaint import ComplaintCreate, ComplaintPublic, ComplaintStats
from app.schemas.discrimination import DiscriminationPublic
from app.schemas.evidence import EvidencePublic
from app.schemas.response import CompanyResponsePublic, ResponseCreate
from app.services.badges import recompute_badges

router = APIRouter(prefix="/companies/{company_id}/complaints", tags=["complaints"])

VISIBLE = (
    VacancyComplaint.moderation_status == "published",
    VacancyComplaint.hidden_at.is_(None),
    VacancyComplaint.deleted_at.is_(None),
)


def to_public(
    complaint: VacancyComplaint,
    pseudonym: str,
    response: CompanyResponse | None = None,
    discrimination: list[DiscriminationDetail] | None = None,
    evidence: list[EvidenceFile] | None = None,
    helpful_count: int = 0,
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
        got_offer=complaint.got_offer,
        difficulty=complaint.difficulty,
        created_at=complaint.created_at,
        company_response=(
            CompanyResponsePublic.model_validate(response) if response else None
        ),
        helpful_count=helpful_count,
        discrimination=[
            DiscriminationPublic.model_validate(d) for d in (discrimination or [])
        ],
        evidence=[EvidencePublic.model_validate(e) for e in (evidence or [])],
    )


@router.post(
    "",
    response_model=ComplaintPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(10, 3600, "complaint_create")],
)
async def create_complaint(
    company: VisibleCompany, data: ComplaintCreate, db: DbSession, user: CurrentUser
) -> ComplaintPublic:
    if user.role != "worker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Шағымды тек жұмысшы-аккаунт қалдыра алады",
        )
    payload = data.model_dump()
    blocks = payload.pop("discrimination")
    complaint = VacancyComplaint(
        company_id=company.id,
        author_id=user.id,
        moderation_status="published",
        **payload,
    )
    db.add(complaint)
    await db.flush()
    details = [
        DiscriminationDetail(complaint_id=complaint.id, **block) for block in blocks
    ]
    db.add_all(details)
    await recompute_badges(db, company.id)
    await db.commit()
    await db.refresh(complaint)
    for detail in details:
        await db.refresh(detail)
    return to_public(complaint, user.pseudonym, None, details)


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
    items = rows.all()
    complaint_ids = [complaint.id for complaint, _, _ in items]
    details_by_complaint: dict[uuid.UUID, list[DiscriminationDetail]] = {}
    evidence_by_complaint: dict[uuid.UUID, list[EvidenceFile]] = {}
    votes_by_complaint: dict[uuid.UUID, int] = {}
    if complaint_ids:
        details = await db.scalars(
            select(DiscriminationDetail).where(
                DiscriminationDetail.complaint_id.in_(complaint_ids)
            )
        )
        for detail in details.all():
            details_by_complaint.setdefault(detail.complaint_id, []).append(detail)
        evidence_rows = await db.scalars(
            select(EvidenceFile).where(
                EvidenceFile.complaint_id.in_(complaint_ids),
                EvidenceFile.status == "visible",
            )
        )
        for evidence in evidence_rows.all():
            evidence_by_complaint.setdefault(evidence.complaint_id, []).append(evidence)
        vote_rows = await db.execute(
            select(HelpfulVote.complaint_id, func.count())
            .where(HelpfulVote.complaint_id.in_(complaint_ids))
            .group_by(HelpfulVote.complaint_id)
        )
        votes_by_complaint.update(dict(vote_rows.all()))
    return [
        to_public(
            complaint,
            pseudonym,
            response,
            details_by_complaint.get(complaint.id),
            evidence_by_complaint.get(complaint.id),
            votes_by_complaint.get(complaint.id, 0),
        )
        for complaint, pseudonym, response in items
    ]


@router.post(
    "/{complaint_id}/evidence",
    response_model=EvidencePublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_complaint_evidence(
    company: VisibleCompany,
    complaint_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    user: CurrentUser,
) -> EvidenceFile:
    complaint = await db.get(VacancyComplaint, complaint_id)
    if complaint is None or complaint.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Шағым табылмады"
        )
    if complaint.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Дәлелді тек шағым авторы тіркей алады",
        )
    return await store_upload(db, file, complaint_id=complaint_id)


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
    kind_rows = await db.execute(
        select(DiscriminationDetail.kind, func.count())
        .join(
            VacancyComplaint,
            DiscriminationDetail.complaint_id == VacancyComplaint.id,
        )
        .where(VacancyComplaint.company_id == company.id, *VISIBLE)
        .group_by(DiscriminationDetail.kind)
    )
    by_kind = {kind: count for kind, count in kind_rows.all()}
    return ComplaintStats(
        total=sum(by_category.values()),
        by_category=by_category,
        by_discrimination_kind=by_kind,
    )
