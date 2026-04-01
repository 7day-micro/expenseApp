from uuid import UUID

from typing import Optional
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
    category_id: Optional[int] = None
    amount: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    note: Optional[str] = None
