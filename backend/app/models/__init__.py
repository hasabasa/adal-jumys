"""Барлық модельді бір жерден импорттау: Alembic autogenerate осы пакетті
импорттағанда бүкіл схема Base.metadata-ға тіркеледі."""

from app.models.comment import Comment
from app.models.company import Company, CompanyBadge, CompanyRepresentative
from app.models.complaint import DiscriminationDetail, VacancyComplaint
from app.models.evidence import CompanyResponse, EvidenceFile
from app.models.moderation import Appeal, ModerationAction
from app.models.report import PostReport
from app.models.review import Review, ReviewProblem, VerificationRecord
from app.models.tip import DailyTip
from app.models.user import KarmaEvent, User
from app.models.vote import HelpfulVote

__all__ = [
    "Appeal",
    "Comment",
    "Company",
    "CompanyBadge",
    "CompanyRepresentative",
    "CompanyResponse",
    "DailyTip",
    "DiscriminationDetail",
    "EvidenceFile",
    "HelpfulVote",
    "KarmaEvent",
    "ModerationAction",
    "PostReport",
    "Review",
    "ReviewProblem",
    "User",
    "VacancyComplaint",
    "VerificationRecord",
]
