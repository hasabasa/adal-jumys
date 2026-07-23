from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.user import Token, UserPrivate, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPrivate,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(5, 300, "register")],
)
async def register(data: UserRegister, db: DbSession) -> User:
    taken = await db.scalar(
        select(User).where(
            (User.email == data.email.lower()) | (User.pseudonym == data.pseudonym)
        )
    )
    if taken is not None:
        # Қайсысы бос емесін айтпаймыз: email-тізімді байқап көру шабуылын қиындатады
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл email немесе псевдоним бос емес",
        )
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        pseudonym=data.pseudonym,
        role=data.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post(
    "/login", response_model=Token, dependencies=[rate_limit(10, 60, "login")]
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> Token:
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if (
        user is None
        or not verify_password(form.password, user.password_hash)
        or not user.is_active
        or user.deleted_at is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email немесе пароль қате",
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserPrivate)
async def me(user: CurrentUser) -> User:
    return user
