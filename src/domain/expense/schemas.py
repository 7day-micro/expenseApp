from uuid import UUID

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ExpenseSchema(BaseModel):
    id: int
    user_id: UUID
    category_id: int

    amount: Decimal

    transaction_date: datetime
    created_at: datetime
    updated_at: datetime

    note: str

    class Meta:
        from_attributes = True


class ExpenseCreateSchema(BaseModel):
    user_id: UUID

    category_id: int

    amount: Decimal
    transaction_date: datetime
    note: str
