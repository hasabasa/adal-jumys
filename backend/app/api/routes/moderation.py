import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from fastapi.responses import Response

from app.api.deps import CurrentModerator, CurrentUser, DbSession
from app.api.routes.evidence import serve_file
from app.models import (
    Appeal,
    Comment,
    Company,
    CompanyRepresentative,
    EvidenceFile,
    ModerationAction,
    Review,
    User,
    VacancyComplaint,
    VerificationRecord,
)
from app.schemas.company import RepresentativeQueueItem
from app.schemas.evidence import EvidenceDecision, EvidenceModeratorItem
from app.schemas.moderation import (
    AppealCreate,
    AppealPublic,
    HideRequest,
    ModerationActionPublic,
    OverturnStat,
    VerificationDecision,
    VerificationQueueItem,
)
from app.services.badges import recompute_badges
from app.services.storage import get_storage

router = APIRouter(prefix="/moderation", tags=["moderation"])

TARGETS = {
    "reviews": (Review, "review"),
    "complaints": (VacancyComplaint, "complaint"),
    "comments": (Comment, "comment"),
}

TargetKind = Literal["reviews", "complaints", "comments"]


async def _get_target(
    db: DbSession, target_kind: TargetKind, target_id: uuid.UUID
) -> tuple[Review | VacancyComplaint | Comment, str]:
    model, target_type = TARGETS[target_kind]
    obj = await db.get(model, target_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Контент табылмады"
        )
    return obj, target_type


async def _company_id_of(
    db: DbSession, obj: Review | VacancyComplaint | Comment
) -> uuid.UUID | None:
    """Комментарийдің компаниясы ата-посты арқылы табылады."""
    if not isinstance(obj, Comment):
        return obj.company_id
    if obj.review_id is not None:
        parent = await db.get(Review, obj.review_id)
    else:
        parent = await db.get(VacancyComplaint, obj.complaint_id)
    return parent.company_id if parent else None


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
    company_id = await _company_id_of(db, obj)
    if company_id is not None:
        await _check_conflict_of_interest(db, moderator, company_id)
    obj.hidden_at = datetime.now(timezone.utc)
    obj.hidden_by_id = moderator.id
    obj.hidden_reason = data.reason
    entry = _log_action(db, moderator, "hide", target_type, target_id, data.reason)
    if company_id is not None and not isinstance(obj, Comment):
        await recompute_badges(db, company_id)
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
    company_id = await _company_id_of(db, obj)
    if company_id is not None:
        await _check_conflict_of_interest(db, moderator, company_id)
    obj.hidden_at = None
    obj.hidden_by_id = None
    obj.hidden_reason = None
    entry = _log_action(db, moderator, "unhide", target_type, target_id, data.reason)
    if company_id is not None and not isinstance(obj, Comment):
        await recompute_badges(db, company_id)
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


@router.get("/evidence", response_model=list[EvidenceModeratorItem])
async def evidence_queue(
    db: DbSession,
    moderator: CurrentModerator,
    status_filter: str = Query(default="pending_moderation", alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[EvidenceFile]:
    rows = await db.scalars(
        select(EvidenceFile)
        .where(EvidenceFile.status == status_filter)
        .order_by(EvidenceFile.created_at)
        .limit(limit)
        .offset(offset)
    )
    return list(rows.all())


@router.get("/evidence/{evidence_id}/file")
async def evidence_preview(
    evidence_id: uuid.UUID, db: DbSession, moderator: CurrentModerator
) -> Response:
    """Модератор кез келген (өшірілмеген) дәлелді қарай алады."""
    evidence = await db.get(EvidenceFile, evidence_id)
    if evidence is None or evidence.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Дәлел табылмады"
        )
    return serve_file(evidence)


@router.post(
    "/evidence/{evidence_id}/{decision}", response_model=ModerationActionPublic
)
async def decide_evidence(
    evidence_id: uuid.UUID,
    decision: Literal["approve", "reject"],
    data: EvidenceDecision,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    evidence = await db.get(EvidenceFile, evidence_id)
    if evidence is None or evidence.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Дәлел табылмады"
        )
    if evidence.purpose != "public_evidence":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Верификация-файл бұл жерде қаралмайды (верификация ағыны бар)",
        )
    if evidence.status != "pending_moderation":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Дәлел қаралып қойған (статусы: {evidence.status})",
        )
    company_id = None
    if evidence.review_id is not None:
        review = await db.get(Review, evidence.review_id)
        company_id = review.company_id if review else None
    elif evidence.complaint_id is not None:
        complaint = await db.get(VacancyComplaint, evidence.complaint_id)
        company_id = complaint.company_id if complaint else None
    if company_id is not None:
        await _check_conflict_of_interest(db, moderator, company_id)
    if decision == "approve":
        evidence.status = "visible"
        evidence.pii_masked = data.pii_masked
    else:
        evidence.status = "hidden"
    entry = _log_action(db, moderator, decision, "evidence", evidence_id, data.reason)
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.get("/verifications", response_model=list[VerificationQueueItem])
async def verification_queue(
    db: DbSession,
    moderator: CurrentModerator,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[VerificationQueueItem]:
    rows = await db.execute(
        select(EvidenceFile, Company.name, User.pseudonym)
        .join(Review, EvidenceFile.review_id == Review.id)
        .join(Company, Review.company_id == Company.id)
        .join(User, Review.author_id == User.id)
        .where(
            EvidenceFile.purpose == "verification",
            EvidenceFile.status == "pending_moderation",
        )
        .order_by(EvidenceFile.created_at)
        .limit(limit)
        .offset(offset)
    )
    return [
        VerificationQueueItem(
            review_id=evidence.review_id,
            evidence_id=evidence.id,
            company_name=company_name,
            author_pseudonym=pseudonym,
            created_at=evidence.created_at,
        )
        for evidence, company_name, pseudonym in rows.all()
    ]


@router.post(
    "/verifications/{review_id}/{decision}", response_model=ModerationActionPublic
)
async def decide_verification(
    review_id: uuid.UUID,
    decision: Literal["approve", "reject"],
    data: VerificationDecision,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Отзыв табылмады"
        )
    if review.verification_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Верификация күйі: {review.verification_status}",
        )
    await _check_conflict_of_interest(db, moderator, review.company_id)

    record = VerificationRecord(
        review_id=review_id,
        verified_by_id=moderator.id,
        method=data.method,
        decision="approved" if decision == "approve" else "rejected",
        note=data.reason,
    )
    db.add(record)
    review.verification_status = "verified" if decision == "approve" else "rejected"

    # Минимизация қағидасы: шешім шықты - верификация-файл ДЕРЕУ өшіріледі
    storage = get_storage()
    files = await db.scalars(
        select(EvidenceFile).where(
            EvidenceFile.review_id == review_id,
            EvidenceFile.purpose == "verification",
            EvidenceFile.status != "deleted",
        )
    )
    for evidence in files.all():
        await storage.delete(evidence.s3_key)
        evidence.status = "deleted"
        evidence.deleted_at = datetime.now(timezone.utc)

    entry = _log_action(
        db, moderator, "verify_review", "review", review_id, data.reason
    )
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.post(
    "/actions/{action_id}/appeal",
    response_model=AppealPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_appeal(
    action_id: uuid.UUID, data: AppealCreate, db: DbSession, user: CurrentUser
) -> Appeal:
    action = await db.get(ModerationAction, action_id)
    if action is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Әрекет табылмады"
        )
    existing = await db.scalar(
        select(Appeal).where(
            Appeal.action_id == action_id,
            Appeal.appellant_id == user.id,
            Appeal.status == "open",
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл әрекетке ашық апелляцияңыз бар",
        )
    appeal = Appeal(action_id=action_id, appellant_id=user.id, body=data.body)
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)
    return appeal


@router.get("/appeals", response_model=list[AppealPublic])
async def appeal_queue(
    db: DbSession,
    moderator: CurrentModerator,
    status_filter: str = Query(default="open", alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[Appeal]:
    rows = await db.scalars(
        select(Appeal)
        .where(Appeal.status == status_filter)
        .order_by(Appeal.created_at)
        .limit(limit)
        .offset(offset)
    )
    return list(rows.all())


@router.post(
    "/appeals/{appeal_id}/{decision}", response_model=ModerationActionPublic
)
async def resolve_appeal(
    appeal_id: uuid.UUID,
    decision: Literal["uphold", "overturn"],
    data: HideRequest,
    db: DbSession,
    moderator: CurrentModerator,
) -> ModerationActionPublic:
    appeal = await db.get(Appeal, appeal_id)
    if appeal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Апелляция табылмады"
        )
    if appeal.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Апелляция қаралып қойған (статусы: {appeal.status})",
        )
    action = await db.get(ModerationAction, appeal.action_id)
    # Екі адам қағидасы: өз шешіміне апелляцияны өзі қарай алмайды
    if action is not None and action.actor_id == moderator.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Өз әрекетіңізге апелляцияны өзіңіз қарай алмайсыз",
        )
    appeal.status = "upheld" if decision == "uphold" else "overturned"
    appeal.resolved_by_id = moderator.id
    appeal.resolved_at = datetime.now(timezone.utc)
    entry = _log_action(
        db,
        moderator,
        "appeal_uphold" if decision == "uphold" else "appeal_overturn",
        action.target_type if action else "other",
        action.target_id if action else appeal_id,
        data.reason,
    )
    await db.commit()
    await db.refresh(entry)
    return _to_public(entry, moderator.pseudonym)


@router.get("/overturn-stats", response_model=list[OverturnStat])
async def overturn_stats(db: DbSession) -> list[OverturnStat]:
    """Жария метрика: әр модератордың әрекет саны мен бұзылған шешім саны."""
    actions = await db.execute(
        select(User.pseudonym, func.count(ModerationAction.id))
        .join(User, ModerationAction.actor_id == User.id)
        .group_by(User.pseudonym)
    )
    overturned = await db.execute(
        select(User.pseudonym, func.count(Appeal.id))
        .join(ModerationAction, Appeal.action_id == ModerationAction.id)
        .join(User, ModerationAction.actor_id == User.id)
        .where(Appeal.status == "overturned")
        .group_by(User.pseudonym)
    )
    overturned_map = dict(overturned.all())
    return [
        OverturnStat(
            moderator_pseudonym=pseudonym,
            total_actions=total,
            overturned=overturned_map.get(pseudonym, 0),
        )
        for pseudonym, total in actions.all()
    ]


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
