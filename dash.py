import asyncio
import calendar
import datetime
from decimal import Decimal
from typing import TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import SessionLocal
from src.domain.expense.schemas import MetricsOverview, PeriodMetrics, VariationMetrics
from src.models import Expense


class MetricSchema(TypedDict):
    days: dict[datetime.date, int]
    total: Decimal
    average_daily_spent: Decimal


class ExpenseMetricGenerator:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.uid = user_id

    async def get_last_month_dayly_spent(self) -> MetricSchema:

        today = datetime.datetime.now(tz=datetime.UTC).date()

        current_month_first_day = today.replace(day=1)
        passed_month_last_day = current_month_first_day - datetime.timedelta(days=1)
        passed_month_first_day = passed_month_last_day.replace(day=1)

        month_days_count = calendar.monthrange(
            passed_month_first_day.year, month=passed_month_first_day.month
        )[1]

        statement = (
            select(
                func.sum(Expense.amount).label("total"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(
                Expense.user_id == self.uid,
                Expense.transaction_date >= passed_month_first_day,
                Expense.transaction_date < current_month_first_day,
            )
            .group_by(func.date(Expense.transaction_date))
            .order_by(func.date(Expense.transaction_date))
        )

        result = await self.db.execute(statement=statement)

        rows = result.all()

        grand_total = sum(row.total for row in rows)

        avarage_per_day = grand_total / month_days_count

        daily = {row.day: row.total for row in rows}

        return {
            "days": daily,
            "total": grand_total,
            "average_daily_spent": avarage_per_day,
        }

    async def get_current_month_dayly_spent(self) -> MetricSchema:
        today = datetime.datetime.now(tz=datetime.UTC).date()

        current_month_first_day = today.replace(day=1)

        statement = (
            select(
                func.sum(Expense.amount).label("total"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(
                Expense.user_id == self.uid,
                Expense.transaction_date >= current_month_first_day,
                Expense.transaction_date < today,
            )
            .group_by(func.date(Expense.transaction_date))
            .order_by(func.date(Expense.transaction_date))
        )

        res = await self.db.execute(statement=statement)

        rows = res.all()

        grand_total = sum(row.total for row in rows)

        average_daily_spenting = grand_total / today.day

        daily = {row.day: row.total for row in rows}

        return {
            "days": daily,
            "total": grand_total,
            "average_daily_spent": average_daily_spenting,
        }

    async def get_last_week_dayly_spent(self) -> MetricSchema:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)
        passed_week_first_day = current_week_first_day - datetime.timedelta(days=7)

        statement = (
            select(
                func.sum(Expense.amount).label("total"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(
                Expense.user_id == self.uid,
                Expense.transaction_date >= passed_week_first_day,
                Expense.transaction_date < current_week_first_day,
            )
            .order_by(func.date(Expense.transaction_date))
            .group_by(func.date(Expense.transaction_date))
        )

        result = await self.db.execute(statement=statement)

        rows = result.all()
        grand_total = sum(row.total for row in rows)
        daily = {row.day: row.total for row in rows}
        average_daily_spenting = grand_total / 7

        return {
            "days": daily,
            "total": grand_total,
            "average_daily_spent": average_daily_spenting,
        }

    async def get_current_week_dayly_spent(self) -> MetricSchema:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)

        statement = (
            select(
                func.sum(Expense.amount).label("total"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(
                Expense.user_id == self.uid,
                Expense.transaction_date >= current_week_first_day,
                Expense.transaction_date < today,
            )
            .order_by(func.date(Expense.transaction_date))
            .group_by(func.date(Expense.transaction_date))
        )

        result = await self.db.execute(statement=statement)

        rows = result.all()
        grand_total = sum(row.total for row in rows)
        daily = {row.day: row.total for row in rows}
        average_daily_spenting = grand_total / today_weekday

        return {
            "days": daily,
            "total": grand_total,
            "average_daily_spent": average_daily_spenting,
        }

    async def get_category_metrics(self, time_range_stmt):

        from src.domain.category.schemas import CategorySchema
        from src.models import Category

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

        print(statement)

        result = await self.db.execute(statement=statement)

        rows = result.all()

        return [
            {
                "category": CategorySchema.model_validate(row.Category),
                "percentage_of_total": 2,
                "total": row.total,
            }
            for row in rows
        ]

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        return ((current - before) / before) * 100


async def run():
    USER_ID = "a50ed0e8-5f81-47f5-8c30-de68fac05c95"
    async with SessionLocal.begin() as session:
        service = ExpenseMetricGenerator(session, user_id=USER_ID)
        last_month = await service.get_last_month_dayly_spent()
        last_week = await service.get_last_week_dayly_spent()
        current_month = await service.get_current_month_dayly_spent()
        current_week = await service.get_current_week_dayly_spent()

        ## VS ============

        last_week_var_average = ExpenseMetricGenerator.get_past_vs_current(
            last_week.get("average_daily_spent"),
            current_week.get("average_daily_spent"),
        )

        from_last_week_total = ExpenseMetricGenerator.get_past_vs_current(
            last_week.get("total"),
            current_week.get("total"),
        )

        from_last_month_daily = ExpenseMetricGenerator.get_past_vs_current(
            last_month.get("average_daily_spent"),
            current_month.get("average_daily_spent"),
        )
        from_last_month_total = ExpenseMetricGenerator.get_past_vs_current(
            last_month.get("total"),
            current_month.get("total"),
        )

        from pprint import pprint

        pprint(
            last_month.get("days"),
        )

        current_month_metric = PeriodMetrics(
            total=current_month.get("total"),
            daily=current_month.get("days"),
            average_daily=current_month.get("average_daily_spent"),
        )

        last_month_metric = PeriodMetrics(
            average_daily=last_month.get("average_daily_spent"),
            daily=last_month.get("days"),
            total=last_month.get("total"),
        )

        current_week_metric = PeriodMetrics(
            total=current_week.get("total"),
            daily=current_week.get("days"),
            average_daily=current_week.get("average_daily_spent"),
        )

        last_week_metric = PeriodMetrics(
            average_daily=last_week.get("average_daily_spent"),
            daily=last_week.get("days"),
            total=last_week.get("total"),
        )

        variations = VariationMetrics(
            from_last_week_daily=last_week_var_average,
            from_last_week_total=from_last_week_total,
            from_last_month_daily=from_last_month_daily,
            from_last_month_total=from_last_month_total,
        )

        Overview = MetricsOverview(
            current_month=current_month_metric,
            last_month=last_month_metric,
            current_week=current_week_metric,
            last_week=last_week_metric,
            variation=variations,
        ).model_dump_json()

        with open("log.json", "w") as f:
            f.write(Overview)


async def run_categories_extractor():
    USER_ID = "a50ed0e8-5f81-47f5-8c30-de68fac05c95"

    async with SessionLocal.begin() as session:
        service = ExpenseMetricGenerator(session, USER_ID)
        from sqlalchemy import and_

        result = await service.get_category_metrics(
            and_(Expense.transaction_date > datetime.date(2026, 1, 1))
        )

        from pprint import pprint

        pprint(result)


if __name__ == "__main__":
    asyncio.run(run_categories_extractor())
