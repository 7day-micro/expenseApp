from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategorySchema(BaseModel):
    id: int
    user_id: UUID
    name: str
    color_icon: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryCreateSchema(BaseModel):
    name: str
    color_icon: str | None


class CategoryUpdateSchema(BaseModel):
    name: str | None = None
    color_icon: str | None = None
