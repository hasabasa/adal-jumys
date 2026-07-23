import uuid

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, select

from app.api.deps import (
    CurrentUser,
    DbSession,
    VisibleCompany,
    require_approved_representative,
)
from app.api.routes.evidence import store_upload
from app.models import CompanyResponse, DiscriminationDetail, EvidenceFile, Review, User
from app.schemas.discrimination import DiscriminationPublic
from app.schemas.evidence import EvidencePublic
from app.schemas.response import CompanyResponsePublic, ResponseCreate
from app.schemas.review import ReviewCreate, ReviewPublic

router = APIRouter(prefix="/companies/{company_id}/reviews", tags=["reviews"])


def to_public(
    review: Review,
    pseudonym: str,
    response: CompanyResponse | None = None,
    discrimination: list[DiscriminationDetail] | None = None,
    evidence: list[EvidenceFile] | None = None,
) -> ReviewPublic:
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
        company_response=(
            CompanyResponsePublic.model_validate(response) if response else None
        ),
        discrimination=[
            DiscriminationPublic.model_validate(d) for d in (discrimination or [])
        ],
        evidence=[EvidencePublic.model_validate(e) for e in (evidence or [])],
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
    payload = data.model_dump()
    blocks = payload.pop("discrimination")
    review = Review(
        company_id=company.id,
        author_id=user.id,
        moderation_status="published",
        **payload,
    )
    db.add(review)
    await db.flush()
    details = [DiscriminationDetail(review_id=review.id, **block) for block in blocks]
    db.add_all(details)
    await db.commit()
    await db.refresh(review)
    for detail in details:
        await db.refresh(detail)
    return to_public(review, user.pseudonym, None, details)


@router.get("", response_model=list[ReviewPublic])
async def list_reviews(
    company: VisibleCompany,
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ReviewPublic]:
    rows = await db.execute(
        select(Review, User.pseudonym, CompanyResponse)
        .join(User, Review.author_id == User.id)
        .outerjoin(
            CompanyResponse,
            and_(
                CompanyResponse.review_id == Review.id,
                CompanyResponse.moderation_status == "published",
            ),
        )
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
    items = rows.all()
    review_ids = [review.id for review, _, _ in items]
    details_by_review: dict[uuid.UUID, list[DiscriminationDetail]] = {}
    evidence_by_review: dict[uuid.UUID, list[EvidenceFile]] = {}
    if review_ids:
        details = await db.scalars(
            select(DiscriminationDetail).where(
                DiscriminationDetail.review_id.in_(review_ids)
            )
        )
        for detail in details.all():
            details_by_review.setdefault(detail.review_id, []).append(detail)
        evidence_rows = await db.scalars(
            select(EvidenceFile).where(
                EvidenceFile.review_id.in_(review_ids),
                EvidenceFile.status == "visible",
            )
        )
        for evidence in evidence_rows.all():
            evidence_by_review.setdefault(evidence.review_id, []).append(evidence)
    return [
        to_public(
            review,
            pseudonym,
            response,
            details_by_review.get(review.id),
            evidence_by_review.get(review.id),
        )
        for review, pseudonym, response in items
    ]


@router.post(
    "/{review_id}/evidence",
    response_model=EvidencePublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_review_evidence(
    company: VisibleCompany,
    review_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    user: CurrentUser,
) -> EvidenceFile:
    review = await db.get(Review, review_id)
    if review is None or review.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв табылмады"
        )
    if review.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Дәлелді тек отзыв авторы тіркей алады",
        )
    return await store_upload(db, file, review_id=review_id)


@router.post(
    "/{review_id}/verification",
    response_model=EvidencePublic,
    status_code=status.HTTP_201_CREATED,
)
async def submit_verification(
    company: VisibleCompany,
    review_id: uuid.UUID,
    file: UploadFile,
    db: DbSession,
    user: CurrentUser,
) -> EvidenceFile:
    """Жұмыс фактісін растау: файл ТЕК модераторға көрінеді, шешімнен кейін
    дереу өшіріледі (verification_record ғана қалады)."""
    review = await db.get(Review, review_id)
    if review is None or review.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв табылмады"
        )
    if review.author_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Верификацияны тек отзыв авторы сұрай алады",
        )
    if review.verification_status != "unverified":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Верификация күйі: {review.verification_status}",
        )
    evidence = await store_upload(
        db, file, review_id=review_id, purpose="verification"
    )
    review.verification_status = "pending"
    await db.commit()
    return evidence


@router.post(
    "/{review_id}/response",
    response_model=CompanyResponsePublic,
    status_code=status.HTTP_201_CREATED,
)
async def respond_to_review(
    company: VisibleCompany,
    review_id: uuid.UUID,
    data: ResponseCreate,
    db: DbSession,
    user: CurrentUser,
) -> CompanyResponse:
    await require_approved_representative(db, company.id, user)
    review = await db.get(Review, review_id)
    if review is None or review.company_id != company.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв табылмады"
        )
    existing = await db.scalar(
        select(CompanyResponse).where(CompanyResponse.review_id == review_id)
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл отзывқа жауап берілген",
        )
    response = CompanyResponse(
        company_id=company.id,
        author_id=user.id,
        review_id=review_id,
        body=data.body,
        moderation_status="published",
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response
