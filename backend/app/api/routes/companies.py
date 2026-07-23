from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DbSession, VisibleCompany, rate_limit
from app.models import Company, CompanyBadge, CompanyRepresentative
from app.schemas.company import (
    BadgePublic,
    CompanyCreate,
    CompanyPublic,
    EmployerRatingPublic,
    RepresentativePublic,
    RepresentativeRequest,
)
from app.services.bin_check import is_valid_bin
from app.services.rating import employer_rating
from app.services.registry import (
    DataEgovRegistryClient,
    NullRegistryClient,
    RegistryInfo,
    get_registry,
)

RegistryDep = Annotated[
    NullRegistryClient | DataEgovRegistryClient, Depends(get_registry)
]

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post(
    "",
    response_model=CompanyPublic,
    status_code=status.HTTP_201_CREATED,
    dependencies=[rate_limit(20, 3600, "company_create")],
)
async def create_company(
    data: CompanyCreate, db: DbSession, user: CurrentUser
) -> Company:
    existing = await db.scalar(select(Company).where(Company.bin == data.bin))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Бұл БСН-мен компания тіркелген",
        )
    company = Company(
        bin=data.bin,
        name=data.name,
        city=data.city,
        address=data.address,
        two_gis_url=str(data.two_gis_url) if data.two_gis_url else None,
        website=str(data.website) if data.website else None,
        instagram_url=str(data.instagram_url) if data.instagram_url else None,
        source="user_created",
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company


@router.get("", response_model=list[CompanyPublic])
async def list_companies(
    db: DbSession,
    search: str | None = Query(default=None, max_length=300),
    city: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[Company]:
    query = select(Company).where(Company.hidden_at.is_(None))
    if search:
        query = query.where(
            or_(Company.name.ilike(f"%{search}%"), Company.bin == search)
        )
    if city:
        query = query.where(Company.city.ilike(city))
    query = query.order_by(Company.name).limit(limit).offset(offset)
    return list((await db.scalars(query)).all())


@router.get(
    "/lookup/{company_bin}",
    response_model=RegistryInfo,
    dependencies=[rate_limit(30, 60, "lookup")],
)
async def lookup_bin(company_bin: str, registry: RegistryDep) -> RegistryInfo:
    """Форма-автотолтыру: реестрден компания мәліметін тарту.

    Реестр қосылмаған/таппаған кезде 404: юзер қолмен енгізе береді.
    """
    if not is_valid_bin(company_bin):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="БСН жарамсыз (чексум сәйкес емес)",
        )
    info = await registry.lookup(company_bin)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Реестрден табылмады, мәліметті қолмен енгізіңіз",
        )
    return info


@router.get("/{company_id}", response_model=CompanyPublic)
async def get_company(company: VisibleCompany) -> Company:
    return company


@router.post(
    "/{company_id}/representatives",
    response_model=RepresentativePublic,
    status_code=status.HTTP_201_CREATED,
)
async def request_representation(
    company: VisibleCompany,
    data: RepresentativeRequest,
    db: DbSession,
    user: CurrentUser,
) -> CompanyRepresentative:
    if user.role != "company":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Өкілдікті тек компания-аккаунт сұрай алады",
        )
    existing = await db.scalar(
        select(CompanyRepresentative).where(
            CompanyRepresentative.company_id == company.id,
            CompanyRepresentative.user_id == user.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Өтініміңіз бар (статусы: {existing.status})",
        )
    representative = CompanyRepresentative(
        company_id=company.id, user_id=user.id, proof_method=data.proof_method
    )
    db.add(representative)
    await db.commit()
    await db.refresh(representative)
    return representative


@router.get("/{company_id}/rating", response_model=EmployerRatingPublic)
async def get_employer_rating(
    company: VisibleCompany, db: DbSession
) -> EmployerRatingPublic:
    result = await employer_rating(db, company.id)
    return EmployerRatingPublic.model_validate(result)


@router.get("/{company_id}/badges", response_model=list[BadgePublic])
async def get_badges(company: VisibleCompany, db: DbSession) -> list[CompanyBadge]:
    rows = await db.scalars(
        select(CompanyBadge).where(
            CompanyBadge.company_id == company.id,
            CompanyBadge.revoked_at.is_(None),
        )
    )
    return list(rows.all())
