import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Company, CompanyRepresentative, User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Жарамсыз немесе мерзімі өткен токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_error
    user = await db.get(User, user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_moderator(user: CurrentUser) -> User:
    if user.trust_level not in ("moderator", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Бұл әрекетке модератор құқығы керек",
        )
    return user


CurrentModerator = Annotated[User, Depends(get_current_moderator)]


async def get_visible_company(company_id: uuid.UUID, db: DbSession) -> Company:
    """Path-тағы company_id бойынша жасырылмаған компанияны табады."""
    company = await db.get(Company, company_id)
    if company is None or company.hidden_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Компания табылмады"
        )
    return company


VisibleCompany = Annotated[Company, Depends(get_visible_company)]


async def require_approved_representative(
    db: AsyncSession, company_id: uuid.UUID, user: User
) -> None:
    """Ресми жауап - тек модератор растаған компания-өкілден."""
    approved = await db.scalar(
        select(CompanyRepresentative.id).where(
            CompanyRepresentative.company_id == company_id,
            CompanyRepresentative.user_id == user.id,
            CompanyRepresentative.status == "approved",
        )
    )
    if approved is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Жауапты тек компанияның расталған өкілі бере алады",
        )
