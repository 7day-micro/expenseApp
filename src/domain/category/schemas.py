from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: UUID
    name: str
    color_icon: str | None
    created_at: datetime
    updated_at: datetime


class CategoryCreateSchema(BaseModel):
    name: str
    color_icon: str | None


class CategoryUpdateSchema(BaseModel):
    name: str | None = None
    color_icon: str | None = None
