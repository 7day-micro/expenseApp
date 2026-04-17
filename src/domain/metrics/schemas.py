from __future__ import annotations

import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.domain.budget.schemas import BudgetSchema
from src.domain.category.schemas import CategorySchema
from src.domain.expense.schemas import SimplifiedExpenseSchema

# ======================================================================
# KPI SCHEMAS
# #====================================================================


class PeakSpendingDay(BaseModel):
    date: datetime.date


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
    daily: list[DailyMetric]
    category_metrics: list[CategoryMetricSchema] | None = []
    # peak_spending: PeakSpendingDay | None = None
    projection: Decimal | None = None
    total_transaction: int = 0


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

    last_12_months: dict[datetime.date, PeriodMetrics]
    selected_range: list[DailyMetric]


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
    transaction_count: int


class DailyMetric(BaseModel):
    date: datetime.date | None = None
    total_transactions: int | None = None
    transaction_average: Decimal | None = None
    total_spent: Decimal | None = None
    min: SimplifiedExpenseSchema | None = None
    max: SimplifiedExpenseSchema | None = None
    is_anomaly: bool | None = False
