import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, VisibleCompany, rate_limit
from app.models import Comment, Review, User, VacancyComplaint
from app.schemas.comment import CommentCreate, CommentPublic

router = APIRouter(tags=["comments"])

COMMENT_VISIBLE = (
    Comment.moderation_status == "published",
    Comment.hidden_at.is_(None),
    Comment.deleted_at.is_(None),
)


async def _get_visible_target(
    db: DbSession,
    company_id: uuid.UUID,
    review_id: uuid.UUID | None,
    complaint_id: uuid.UUID | None,
) -> None:
    if review_id is not None:
        target = await db.get(Review, review_id)
    else:
        target = await db.get(VacancyComplaint, complaint_id)
    if (
        target is None
        or target.company_id != company_id
        or target.moderation_status != "published"
        or target.hidden_at is not None
        or target.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Пост табылмады"
        )


async def _create(
    db: DbSession,
    user: User,
    data: CommentCreate,
    review_id: uuid.UUID | None = None,
    complaint_id: uuid.UUID | None = None,
) -> CommentPublic:
    comment = Comment(
        review_id=review_id,
        complaint_id=complaint_id,
        author_id=user.id,
        body=data.body,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return CommentPublic(
        id=comment.id,
        author_pseudonym=user.pseudonym,
        body=comment.body,
        created_at=comment.created_at,
    )


async def _list(
    db: DbSession,
    limit: int,
    offset: int,
    review_id: uuid.UUID | None = None,
    complaint_id: uuid.UUID | None = None,
) -> list[CommentPublic]:
    query = (
        select(Comment, User.pseudonym)
        .join(User, Comment.author_id == User.id)
        .where(*COMMENT_VISIBLE)
        .order_by(Comment.created_at)
        .limit(limit)
        .offset(offset)
    )
    if review_id is not None:
        query = query.where(Comment.review_id == review_id)
    else:
        query = query.where(Comment.complaint_id == complaint_id)
    rows = await db.execute(query)
    return [
        CommentPublic(
            id=comment.id,
            author_pseudonym=pseudonym,
            body=comment.body,
            created_at=comment.created_at,
        )
        for comment, pseudonym in rows.all()
    ]


@router.post(
    "/companies/{company_id}/reviews/{review_id}/comments",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(20, 3600, "comment_create")],
)
async def comment_review(
    company: VisibleCompany,
    review_id: uuid.UUID,
    data: CommentCreate,
    db: DbSession,
    user: CurrentUser,
) -> CommentPublic:
    await _get_visible_target(db, company.id, review_id, None)
    return await _create(db, user, data, review_id=review_id)


@router.get(
    "/companies/{company_id}/reviews/{review_id}/comments",
    response_model=list[CommentPublic],
)
async def list_review_comments(
    company: VisibleCompany,
    review_id: uuid.UUID,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CommentPublic]:
    await _get_visible_target(db, company.id, review_id, None)
    return await _list(db, limit, offset, review_id=review_id)


@router.post(
    "/companies/{company_id}/complaints/{complaint_id}/comments",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(20, 3600, "comment_create")],
)
async def comment_complaint(
    company: VisibleCompany,
    complaint_id: uuid.UUID,
    data: CommentCreate,
    db: DbSession,
    user: CurrentUser,
) -> CommentPublic:
    await _get_visible_target(db, company.id, None, complaint_id)
    return await _create(db, user, data, complaint_id=complaint_id)


@router.get(
    "/companies/{company_id}/complaints/{complaint_id}/comments",
    response_model=list[CommentPublic],
)
async def list_complaint_comments(
    company: VisibleCompany,
    complaint_id: uuid.UUID,
    db: DbSession,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[CommentPublic]:
    await _get_visible_target(db, company.id, None, complaint_id)
    return await _list(db, limit, offset, complaint_id=complaint_id)
