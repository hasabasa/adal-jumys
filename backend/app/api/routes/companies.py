from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DbSession, VisibleCompany
from app.models import Company
from app.schemas.company import CompanyCreate, CompanyPublic

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyPublic, status_code=status.HTTP_201_CREATED)
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


@router.get("/{company_id}", response_model=CompanyPublic)
async def get_company(company: VisibleCompany) -> Company:
    return company
