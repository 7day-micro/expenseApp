# Initial schemas

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal


class BudgetSchema(BaseModel):
    id: int
    amount_limit: Decimal

    created_at: datetime
    budget_date: datetime

    user_id: int
    category_id: Optional[int]

    class Meta:
        from_attributes = True


class BudgetCreateSchema(BaseModel):
    budget_date: datetime
    user_id: int
    category_id: Optional[int]
