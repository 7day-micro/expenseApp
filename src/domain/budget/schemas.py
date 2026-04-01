from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal

from uuid import UUID


class BudgetSchema(BaseModel):
    model_config = ConfigDict(from_attributes = True, extra='forbid' )

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
    model_config = ConfigDict(from_attributes = True, extra='forbid' )

    user_id: UUID
    category_id: Optional[int]
    amount_limit: Decimal
    month_year: datetime

class BudgetUpdateSchema(BaseModel):
    model_config = ConfigDict(from_attributes = True, extra='forbid' )

    user_id: UUID|None = None
    category_id: Optional[int]|None = None
    amount_limit: Decimal|None = None
    month_year: datetime|None = None


