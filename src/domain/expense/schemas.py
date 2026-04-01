from uuid import UUID

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from decimal import Decimal


class ExpenseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: UUID
    category_id: int
    amount: Decimal
    transaction_date: datetime
    created_at: datetime
    updated_at: datetime
    note: str


class ExpenseCreateSchema(BaseModel):
    category_id: int
    amount: Decimal
    transaction_date: datetime
    note: str


class ExpenseUpdateSchema(BaseModel):
    category_id: int | None = None
    amount: Decimal | None = None
    transaction_date: datetime | None = None
    note: str | None = None
