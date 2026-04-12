from uuid import UUID

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class CategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: UUID
    name: str
    color_icon: Optional[str]
    created_at: datetime
    updated_at: datetime



class CategoryCreateSchema(BaseModel):
    name: str
    color_icon: Optional[str]


class CategoryUpdateSchema(BaseModel):
    name: Optional[str] = None
    color_icon: Optional[str] = None
