from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.budget.schemas import BudgetSchema
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


# ======================================================================
# KPI SCHEMAS
# #====================================================================


class PeriodMetrics(BaseModel):
    average_daily: Decimal
    total: Decimal
    daily: dict[date, Decimal]


class VariationMetrics(BaseModel):
    from_last_week_total: Decimal
    from_last_week_daily: Decimal
    from_last_month_total: Decimal
    from_last_month_daily: Decimal


class MetricsOverview(BaseModel):
    current_month: PeriodMetrics
    last_month: PeriodMetrics

    current_week: PeriodMetrics
    last_week: PeriodMetrics

    variation: VariationMetrics

    # COMPARACION
    # last_month_vs_current_month_average_daily_spent: Decimal | None
    # last_week_vs_current_week_average_daily_spent: Decimal | None


class BudgetMetricSchema(BaseModel):
    budget: BudgetSchema
    percentage_used: Decimal
    spent: Decimal
    limit: Decimal


class CategoryMetricSchema(BaseModel):
    category: CategorySchema
    percentage_of_total: Decimal
    total_spent: Decimal
