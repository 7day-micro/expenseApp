import asyncio
import calendar
import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, and_, text, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import SessionLocal
from src.domain.expense.schemas import CategoryMetricSchema, CategorySchema
from src.domain.expense.schemas import PeriodMetrics
from src.models import Category
from src.models import Expense
import calendar
import datetime
from decimal import Decimal
from math import ceil
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, and_, extract, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_service import BaseService
from src.db import SessionLocal
from src.domain.category.schemas import CategorySchema
from src.domain.category.service import CategoryService
from src.domain.expense.schemas import CategoryMetricSchema
from src.domain.expense.schemas import DailyMetrics
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    PaginatedResponseSchema,
    PeriodMetrics,
)
from src.domain.expense.schemas import MetaSchema
from src.domain.expense.schemas import (
    VariationMetrics,
    MetricsOverview,
    BudgetMetricSchema,
)
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Category
from src.models import Expense
from src.models import Budget


class ExpenseMetricGenerator:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.uid = user_id

    @property
    def past_month_range_statement(self):
        today = datetime.datetime.now(tz=datetime.UTC).date()

        current_month_first_day = today.replace(day=1)
        passed_month_last_day = current_month_first_day - datetime.timedelta(days=1)
        passed_month_first_day = passed_month_last_day.replace(day=1)

        month_days_count = calendar.monthrange(
            passed_month_first_day.year, month=passed_month_first_day.month
        )[1]
        return and_(
            Expense.transaction_date >= passed_month_first_day,
            Expense.transaction_date < current_month_first_day,
        )

    @property
    def current_month_range_statement(self):
        today = datetime.datetime.now(tz=datetime.UTC).date()
        tomorrow = today + datetime.timedelta(days=1)

        current_month_first_day = today.replace(day=1)

        return and_(
            Expense.transaction_date >= current_month_first_day,
            Expense.transaction_date < tomorrow,
        )

    @property
    def last_week_range_statement(self):
        today = datetime.datetime.now(tz=datetime.UTC).date()
        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)
        passed_week_first_day = current_week_first_day - datetime.timedelta(days=7)

        return and_(
            Expense.transaction_date >= passed_week_first_day,
            Expense.transaction_date < current_week_first_day,
        )

    @property
    def current_week_range_statement(self):
        today = datetime.datetime.now(tz=datetime.UTC).date()
        tomorrow = today + datetime.timedelta(days=1)

        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)

        return and_(
            Expense.transaction_date >= current_week_first_day,
            Expense.transaction_date < tomorrow,
        )

    def get_statement(self, range_statement):
        return (
            select(
                func.sum(Expense.amount).label("total"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(Expense.user_id == self.uid, range_statement)
            .group_by(func.date(Expense.transaction_date))
            .order_by(func.date(Expense.transaction_date))
        )

    async def get_last_month_daily_spent(self) -> PeriodMetrics:
        stmt = self.get_statement(self.past_month_range_statement)

        result = await self.db.execute(statement=stmt)

        rows = result.all()

        grand_total = rows[0].grand_total if rows else Decimal(0)

        average_per_day = Decimal(grand_total / len(rows)).quantize(Decimal("0.00"))

        daily = {row.day: Decimal(row.total).quantize(Decimal("0.00")) for row in rows}

        category_metrics = await self.get_category_metrics(
            self.past_month_range_statement
        )

        return PeriodMetrics(
            daily=daily,
            average_daily=average_per_day,
            total=grand_total,
            category_metrics=category_metrics,
        )

    async def get_current_month_daily_spent(self) -> PeriodMetrics:
        stmt = self.get_statement(self.current_month_range_statement)

        category_metrics = await self.get_category_metrics(
            self.current_month_range_statement
        )

        res = await self.db.execute(statement=stmt)

        rows = res.all()

        grand_total = rows[0].grand_total if rows else Decimal(0)

        average_daily_spending = (
            grand_total / datetime.datetime.now(tz=datetime.UTC).date().day
        )

        daily = {row.day: row.total for row in rows}

        return PeriodMetrics(
            daily=daily,
            average_daily=average_daily_spending,
            total=grand_total,
            category_metrics=category_metrics,
        )

    async def get_last_week_daily_spent(self) -> PeriodMetrics:
        stmt = self.get_statement(self.last_week_range_statement)

        result = await self.db.execute(statement=stmt)

        rows = result.all()
        grand_total = rows[0].grand_total if rows else Decimal(0)
        daily = {row.day: row.total for row in rows}
        average_daily_spending = grand_total / 7

        category_metrics = await self.get_category_metrics(
            self.last_week_range_statement
        )

        return PeriodMetrics(
            daily=daily,
            average_daily=average_daily_spending,
            total=grand_total,
            category_metrics=category_metrics,
        )

    async def get_current_week_daily_spent(self) -> PeriodMetrics:
        stmt = self.get_statement(self.current_week_range_statement)

        result = await self.db.execute(statement=stmt)

        rows = result.all()
        grand_total = rows[0].grand_total if rows else Decimal(0)
        daily = {row.day: row.total for row in rows}

        average_daily_spending = (
            grand_total / datetime.datetime.now(tz=datetime.UTC).date().isoweekday()
        )

        category_metrics = await self.get_category_metrics(
            time_range_stmt=self.current_month_range_statement
        )

        return PeriodMetrics(
            daily=daily,
            total=grand_total,
            average_daily=average_daily_spending,
            category_metrics=category_metrics,
        )

    async def get_category_metrics(self, time_range_stmt) -> list[CategoryMetricSchema]:
        grand_total_st = (
            select(func.sum(Expense.amount))
            .where(time_range_stmt, Expense.user_id == self.uid)
            .scalar_subquery()
        )

        statement = (
            select(
                Category.name.label("cat_name"),
                func.sum(Expense.amount).label("total"),
                grand_total_st.label("grand_total"),
                Category,
            )
            .join(Category, Expense.category_id == Category.id)
            .where(
                Expense.user_id == self.uid,
                Expense.category_id.isnot(None),
                time_range_stmt,
            )
            .group_by(Category.id)
        )

        result = await self.db.execute(statement=statement)

        rows = result.all()

        return [
            CategoryMetricSchema(
                total=row.total,
                category=CategorySchema.model_validate(row.Category),
                percentage_of_total=ExpenseMetricGenerator.get_percentage_of_total(
                    row.grand_total, row.total
                ),
            )
            for row in rows
        ]

    @staticmethod
    def get_percentage_of_total(total: Decimal, part: Decimal):
        return Decimal((part / max(1, total)) * 100).quantize(Decimal("0.00"))

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        """

        Return the variont for before and after
        """
        return ((current - before) / (before if before != 0 else 1)) * 100

    async def get_budgte_metrics(self):

        today = datetime.datetime.now(tz=datetime.UTC).date()

        statement = (
            select(
                Budget,  # Budget it self
                Budget.category_id.label("cat_id"),  # category id
                func.sum(Expense.amount).label("spent"),  # sum of all expenses
                Budget.amount_limit,  # Budget target amount
                (func.sum(Expense.amount / Budget.amount_limit * 100)).label(
                    "total_used"
                ),  # total of use in percentage of all expenses agaisnt the amount limit
                (func.avg(Expense.amount)).label("average"),  # Average amount of spends
            )
            .join(
                Expense,
                and_(
                    Budget.category_id == Expense.category_id,
                    Budget.month_year <= Expense.transaction_date,
                    Expense.transaction_date
                    < Budget.month_year + text("INTERVAL '1 MONTH'"),
                ),
                isouter=True,
            )
            .where(
                extract("month", Budget.month_year) == today.month,
                extract("year", Budget.month_year) == today.year,
            )
            .group_by(Budget.id)
        )

        rows = await self.db.execute(statement=statement)

        return [
            BudgetMetricSchema(
                budget=row.Budget,
                limit=row.amount_limit,
                percentage_used=row.total_used or Decimal(0),
                spending_average=row.average or Decimal(0),
                spent=row.spent or Decimal(0),
            )
            for row in rows
        ]


async def run_budget_extractor():
    USER_ID = "26089e8a-f002-4495-b420-0c2edde4e913"

    async with SessionLocal.begin() as session:
        service = ExpenseMetricGenerator(session, USER_ID)

        from pprint import pprint

        res = await service.get_budgte_metrics()
        pprint(res)


if __name__ == "__main__":
    asyncio.run(run_budget_extractor())
