from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Kind = Literal[
    "language",
    "age",
    "gender",
    "ethnicity",
    "religion",
    "pregnancy",
    "disability",
    "appearance",
    "other",
    "bullying",
    "dignity_abuse",
    "sexual_harassment",
    "threats",
    "extortion",
]
Form = Literal["vacancy_text", "interview", "at_work"]


class DiscriminationCreate(BaseModel):
    kind: Kind
    form: Form
    description: str | None = Field(default=None, max_length=2000)


class DiscriminationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kind: str
    form: str
    description: str | None
