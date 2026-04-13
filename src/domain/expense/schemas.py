from datetime import date, datetime
from decimal import Decimal
from typing import Any
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


class DailyMetrics(BaseModel):
    total: Decimal
    count: int

class PeakSpendingDay(DailyMetrics):
    date : date



class PeriodMetrics(BaseModel):
    """
    This schema is for the scerios where we want to present some data about a
    certain period of time, i.e a week, a month, whatever.

    The intention is to given metrics about this period of time, such as:

    average_daily = The average spenting per day
    total = the total transactioned between the given range of time
    daily = a list of dict where the date is the key and has the amount of the total transactioned in that day
    """

    average_daily: Decimal
    total: Decimal
    daily: dict[date, DailyMetrics]
    category_metrics: list[CategoryMetricSchema] | None = []
    peak_spending : PeakSpendingDay | None = None
    projection : Decimal | None = None
    total_transaction : int = 0


class VariationMetrics(BaseModel):
    """
    This schema is for deliver data about variation between to period of time

    for example, the last week vs, this current week

    In nutshell how many % of variation from the last period to this current period
    """

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

    budgets_metrics: list[BudgetMetricSchema]


class BudgetMetricSchema(BaseModel):
    budget: BudgetSchema
    percentage_used: Decimal
    limit: Decimal
    spent: Decimal
    spending_average: Decimal


class CategoryMetricSchema(BaseModel):
    category: CategorySchema
    percentage_of_total: Decimal
    total: Decimal
    transaction_count : int


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
