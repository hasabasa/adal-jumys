import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=2, max_length=1000)


class CommentPublic(BaseModel):
    id: uuid.UUID
    author_pseudonym: str
    body: str
    created_at: datetime
