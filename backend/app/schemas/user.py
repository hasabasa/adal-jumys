import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# Псевдоним: әріп/цифр/астыңғы сызық, 3-30 таңба.
# Нақты аты-жөнге ұқсамау тексерісі модерация деңгейінде.
PSEUDONYM_PATTERN = r"^[a-zA-Z0-9_Ѐ-ӿӘәҒғҚқҢңӨөҰұҮүҺһІі]{3,30}$"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    pseudonym: str = Field(pattern=PSEUDONYM_PATTERN)
    role: Literal["worker", "company"]


class UserPublic(BaseModel):
    """Жария профиль: тек псевдоним мен статистика, ешқандай жеке дерек."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pseudonym: str
    role: str
    trust_level: str
    karma: int


class UserPrivate(UserPublic):
    """Юзердің ӨЗІНЕ ғана қайтарылатын профиль."""

    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
