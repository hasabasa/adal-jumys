"""Барлық модельді бір жерден импорттау: Alembic autogenerate осы пакетті
импорттағанда бүкіл схема Base.metadata-ға тіркеледі."""

from app.models.company import Company, CompanyBadge, CompanyRepresentative
from app.models.complaint import DiscriminationDetail, VacancyComplaint
from app.models.evidence import CompanyResponse, EvidenceFile
from app.models.moderation import Appeal, ModerationAction
from app.models.review import Review, VerificationRecord
from app.models.tip import DailyTip
from app.models.user import KarmaEvent, User

__all__ = [
    "Appeal",
    "Company",
    "CompanyBadge",
    "CompanyRepresentative",
    "CompanyResponse",
    "DailyTip",
    "DiscriminationDetail",
    "EvidenceFile",
    "KarmaEvent",
    "ModerationAction",
    "Review",
    "User",
    "VacancyComplaint",
    "VerificationRecord",
]
