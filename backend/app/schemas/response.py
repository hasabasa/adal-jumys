from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResponseCreate(BaseModel):
    body: str = Field(min_length=20, max_length=5000)


class CompanyResponsePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    body: str
    created_at: datetime
