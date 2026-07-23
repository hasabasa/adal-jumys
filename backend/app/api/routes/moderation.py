import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentModerator, DbSession
from app.models import (
    Company,
    CompanyRepresentative,
    ModerationAction,
    Review,
    User,
    VacancyComplaint,
)
from app.schemas.company import RepresentativeQueueItem
from app.schemas.moderation import HideRequest, ModerationActionPublic

router = APIRouter(prefix="/moderation", tags=["moderation"])

TARGETS = {
    "reviews": (Review, "review"),
    "complaints": (VacancyComplaint, "complaint"),
}

TargetKind = Literal["reviews", "complaints"]


async def _get_target(
    db: DbSession, target_kind: TargetKind, target_id: uuid.UUID
) -> tuple[Review | VacancyComplaint, str]:
    model, target_type = TARGETS[target_kind]
    obj = await db.get(model, target_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Контент табылмады"
        )
    return obj, target_type


async def _check_conflict_of_interest(
    db: DbSession, moderator: User, company_id: uuid.UUID
) -> None:
    """Брифтегі автоблок: модератор өзі отзыв/шағым қалдырған компанияның
    контентін модерациялай алмайды."""
    own_content = await db.scalar(
        select(Review.id)
        .where(Review.company_id == company_id, Review.author_id == moderator.id)
        .union_all(
            select(VacancyComplaint.id).where(
                VacancyComplaint.company_id == company_id,
                VacancyComplaint.author_id == moderator.id,
            )
        )
        .limit(1)
    )
    if own_content is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Мүдде қақтығысы: бұл компанияға өз отзывыңыз/шағымыңыз бар",
        )


def _log_action(
    db: DbSession, moderator: User, action: str, target_type: str, target_id: uuid.UUID, reason: str
) -> ModerationAction:
    entry = ModerationAction(
        actor_id=moderator.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
    )
    db.add(entry)
    return entry


def _to_public(entry: ModerationAction, pseudonym: str | None) -> ModerationActionPublic:
    return ModerationActionPublic(
        id=entry.id,
        actor_pseudonym=pseudonym,
        action=entry.action,
        target_type=entry.target_type,
        target_id=entry.target_id,
        reason=entry.reason,
        created_at=entry.created_at,
    )


@router.post("/{target_kind}/{target_id}/hide", response_model=ModerationActionPublic)
async def hide_content(
    target_kind: TargetKind,
    target_id: uuid.UUID,
    data: HideRequest,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    obj, target_type = await _get_target(db, target_kind, target_id)
    if obj.hidden_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Контент онсыз да жасырулы"
        )
    await _check_conflict_of_interest(db, moderator, obj.company_id)
    obj.hidden_at = datetime.now(timezone.utc)
    obj.hidden_by_id = moderator.id
    obj.hidden_reason = data.reason
    entry = _log_action(db, moderator, "hide", target_type, target_id, data.reason)
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.post("/{target_kind}/{target_id}/unhide", response_model=ModerationActionPublic)
async def unhide_content(
    target_kind: TargetKind,
    target_id: uuid.UUID,
    data: HideRequest,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    obj, target_type = await _get_target(db, target_kind, target_id)
    if obj.hidden_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Контент жасырулы емес"
        )
    await _check_conflict_of_interest(db, moderator, obj.company_id)
    obj.hidden_at = None
    obj.hidden_by_id = None
    obj.hidden_reason = None
    entry = _log_action(db, moderator, "unhide", target_type, target_id, data.reason)
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.get("/representatives", response_model=list[RepresentativeQueueItem])
async def representative_queue(
    db: DbSession,
    moderator: CurrentModerator,
    status_filter: str = Query(default="pending", alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[RepresentativeQueueItem]:
    rows = await db.execute(
        select(CompanyRepresentative, Company.name, User.pseudonym)
        .join(Company, CompanyRepresentative.company_id == Company.id)
        .join(User, CompanyRepresentative.user_id == User.id)
        .where(CompanyRepresentative.status == status_filter)
        .order_by(CompanyRepresentative.created_at)
        .limit(limit)
        .offset(offset)
    )
    return [
        RepresentativeQueueItem(
            id=rep.id,
            company_name=company_name,
            user_pseudonym=pseudonym,
            proof_method=rep.proof_method,
            status=rep.status,
            created_at=rep.created_at,
        )
        for rep, company_name, pseudonym in rows.all()
    ]


@router.post(
    "/representatives/{representative_id}/{decision}",
    response_model=ModerationActionPublic,
)
async def decide_representation(
    representative_id: uuid.UUID,
    decision: Literal["approve", "reject"],
    data: HideRequest,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    rep = await db.get(CompanyRepresentative, representative_id)
    if rep is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Өтінім табылмады"
        )
    if rep.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Өтінім қаралып қойған (статусы: {rep.status})",
        )
    rep.status = "approved" if decision == "approve" else "rejected"
    rep.reviewed_by_id = moderator.id
    rep.reviewed_at = datetime.now(timezone.utc)
    entry = _log_action(
        db, moderator, decision, "representative", representative_id, data.reason
    )
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.get("/log", response_model=list[ModerationActionPublic])
async def public_log(
    db: DbSession,
    target_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ModerationActionPublic]:
    """Ашық аудит-лог: авторизациясыз-ақ көрінеді (модерация да ашық)."""
    query = (
        select(ModerationAction, User.pseudonym)
        .join(User, ModerationAction.actor_id == User.id, isouter=True)
        .order_by(ModerationAction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if target_id is not None:
        query = query.where(ModerationAction.target_id == target_id)
    rows = await db.execute(query)
    return [_to_public(entry, pseudonym) for entry, pseudonym in rows.all()]
