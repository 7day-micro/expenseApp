from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from decimal import Decimal

from uuid import UUID


class BudgetSchema(BaseModel):
    id: int
    user_id: UUID
    amount_limit: Decimal

    created_at: datetime
    month_year: datetime

    user_id: int
    category_id: Optional[int]

    class Meta:
        from_attributes = True


class BudgetCreateSchema(BaseModel):
    user_id: UUID
    category_id: Optional[int]
    amount_limit: Decimal
    month_year: datetime
