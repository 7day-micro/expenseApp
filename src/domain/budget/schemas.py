from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str = Field(str, max=60)
    user_id: UUID
    amount_limit: Decimal

    created_at: datetime
    month_year: datetime

    category_id: int | None


class BudgetCreateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str = Field(min_length=1, max_length=60)
    category_id: int | None
    amount_limit: Decimal
    month_year: datetime


class BudgetUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    name: str | None = Field(default=None, min_length=1, max_length=60)
    category_id: int | None = None
    amount_limit: Decimal | None = None
    month_year: datetime | None = None
