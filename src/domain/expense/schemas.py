from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.category.schemas import CategorySchema


class ExpenseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    amount: Decimal
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime
    note: str

    category: CategorySchema | None = None


class SimplifiedExpenseSchema(BaseModel):
    id: int
    amount: Decimal
    category_name: str | None = None


class ExpenseCreateSchema(BaseModel):
    category_id: int | None = None
    amount: Decimal
    transaction_date: datetime
    note: str


class ExpenseUpdateSchema(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = None
    transaction_date: datetime | None = None
    note: str | None = None


class MetaSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    count: int
    page: int
    total_pages: int


class PaginatedResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    data: list[ExpenseSchema]
    meta: MetaSchema
