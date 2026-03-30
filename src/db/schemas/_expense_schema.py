# Initial schemas

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ExpenseSchema(BaseModel):
    id: int
    amount: Decimal

    user_id: int
    category_id: int

    transaction_date: datetime
    created_at: datetime

    note: str

    class Meta:
        from_attributes = True


class ExpenseCreateSchema(BaseModel):
    amount: Decimal
    user_id: int
    category_id: int
    transaction_date: datetime
    note: str
