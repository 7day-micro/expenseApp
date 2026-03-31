from uuid import UUID

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CategorySchema(BaseModel):
    id: int
    user_id: UUID
    name: str
    color_icon: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Meta:
        from_attributes = True


class CategoryCreateSchema(BaseModel):
    name: str
    color_icon: Optional[str]
    user_id: UUID
