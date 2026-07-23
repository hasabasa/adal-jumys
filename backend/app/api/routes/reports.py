import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, rate_limit
from app.api.routes.evidence import store_upload
from app.models import (
    Comment,
    CompanyRepresentative,
    PostReport,
    Review,
    VacancyComplaint,
)
from app.schemas.evidence import EvidencePublic

router = APIRouter(tags=["reports"])

TARGET_MODELS = {
    "reviews": Review,
    "complaints": VacancyComplaint,
    "comments": Comment,
}

USER_REASONS = ("pii_exposed", "insult", "spam", "defamation", "other")
COMPANY_REASONS = ("false_facts", "defamation", "pii_exposed", "fake_evidence", "other")


class ReportCreate(BaseModel):
    target_kind: Literal["reviews", "complaints", "comments"]
    target_id: uuid.UUID
    is_company_claim: bool = False
    reason: str
    body: str | None = Field(default=None, max_length=3000)

    @model_validator(mode="after")
    def validate_track(self) -> "ReportCreate":
        allowed = COMPANY_REASONS if self.is_company_claim else USER_REASONS
        if self.reason not in allowed:
            raise ValueError("Себеп осы трекке жатпайды")
        if self.is_company_claim and (self.body is None or len(self.body) < 20):
            raise ValueError("Компания-дауға түсіндірме міндетті (кемінде 20 таңба)")
        return self


class ReportPublic(BaseModel):
    id: uuid.UUID
    status: str
    verified_claim: bool
    created_at: datetime


@router.post(
    "/reports",
    response_model=ReportPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(10, 3600, "report")],
)
async def create_report(
    data: ReportCreate, db: DbSession, user: CurrentUser
) -> ReportPublic:
    model = TARGET_MODELS[data.target_kind]
    target = await db.get(model, data.target_id)
    if (
        target is None
        or target.moderation_status != "published"
        or target.hidden_at is not None
        or target.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост табылмады"
        )

    # Компанияны табу (коммент болса - ата-посты арқылы)
    if isinstance(target, Comment):
        parent = (
            await db.get(Review, target.review_id)
            if target.review_id
            else await db.get(VacancyComplaint, target.complaint_id)
        )
        company_id = parent.company_id if parent else None
    else:
        company_id = target.company_id

    verified_claim = False
    if data.is_company_claim and company_id is not None:
        verified_claim = (
            await db.scalar(
                select(CompanyRepresentative.id).where(
                    CompanyRepresentative.company_id == company_id,
                    CompanyRepresentative.user_id == user.id,
                    CompanyRepresentative.status == "approved",
                )
            )
        ) is not None

    report = PostReport(
        review_id=data.target_id if data.target_kind == "reviews" else None,
        complaint_id=data.target_id if data.target_kind == "complaints" else None,
        comment_id=data.target_id if data.target_kind == "comments" else None,
        reporter_id=user.id,
        is_company_claim=data.is_company_claim,
        verified_claim=verified_claim,
        reason=data.reason,
        body=data.body,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return ReportPublic(
        id=report.id,
        status=report.status,
        verified_claim=report.verified_claim,
        created_at=report.created_at,
    )


@router.post(
    "/reports/{report_id}/evidence",
    response_model=EvidencePublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report_evidence(
    report_id: uuid.UUID, file: UploadFile, db: DbSession, user: CurrentUser
):
    """Кері дәлел: жария емес, тек модератор көреді (purpose='report')."""
    report = await db.get(PostReport, report_id)
    if report is None or report.reporter_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Шағым табылмады"
        )
    if report.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Шағым қаралып қойған"
        )
    return await store_upload(db, file, report_id=report_id, purpose="report")
