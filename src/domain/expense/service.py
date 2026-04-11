import calendar
import datetime
from decimal import Decimal
from typing import Any, TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.base_service import BaseService
from src.domain.category.service import CategoryService
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    MetricsOverview,
    PeriodMetrics,
    VariantionMetrics,
)
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Expense


class ExpenseService(
    BaseService[Expense, ExpenseCreateSchema, ExpenseSchema, ExpenseUpdateSchema]
):
    async def create(self, data: ExpenseCreateSchema, user_id: UUID) -> Expense:

        if data.category_id is not None:
            category_service = CategoryService(self.db)
            await category_service.get_by_id(data.category_id, user_id)

        expense = Expense(**data.model_dump(exclude={"user_id"}))
        expense.user_id = user_id

        self.db.add(expense)
        try:
            await self.db.commit()
            await self.db.refresh(expense)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="Expense",
                details={"user_id": str(user_id), "original_error": str(e)},
            ) from e

        return expense

    async def update(
        self, object_id: Any, data: ExpenseUpdateSchema, user_id: UUID
    ) -> Expense:
        expense = await self.get_by_id(object_id, user_id)

        if data.category_id is not None:
            category_service = CategoryService(self.db)
            await category_service.get_by_id(data.category_id, user_id)

        # Since exclude_none will ignore all fields
        # and sometimes we want get category_id set to None
        # The use of exclude_none here is not suitable
        # So we need to manually loop through the fields and set
        # them if they are not None (except for category_id which can be set to None)

        for key, value in data.model_dump(
            exclude={"user_id"}, exclude_unset=True
        ).items():
            # Ensure only category_id can be set to None, other fields will be ignored if None
            if key == "category_id" and value is None:
                expense.category_id = value
            elif value is not None:
                setattr(expense, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(expense)
            return expense
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="updating",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

    async def delete(self, object_id: Any, user_id: UUID) -> Expense:
        expense = await self.get_by_id(object_id, user_id)

        try:
            await self.db.delete(expense)
            await self.db.commit()
            return expense
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="deleting",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Expense:
        statement = select(Expense).where(
            Expense.id == object_id, Expense.user_id == user_id
        )
        result = await self.db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise EntityNotFoundException(entity_name="Expense", object_id=object_id)

        return expense

    async def get_all(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int | None = None,
        date_filter: datetime.date | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
    ) -> list[Expense]:
        statement = select(Expense).where(Expense.user_id == user_id)

        if date_filter is not None:
            statement = statement.where(
                func.date(Expense.transaction_date) == date_filter
            )
        else:
            if start_date is not None:
                statement = statement.where(
                    func.date(Expense.transaction_date) >= start_date
                )
            if end_date is not None:
                statement = statement.where(
                    func.date(Expense.transaction_date) <= end_date
                )

        if min_value is not None:
            statement = statement.where(Expense.amount >= max(0, min_value))
        if max_value is not None:
            statement = statement.where(Expense.amount <= max(0, max_value))

        statement = statement.order_by(
            Expense.transaction_date.desc(), Expense.id.desc()
        )

        if skip:
            statement = statement.offset(skip)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.db.execute(statement)
        return list(result.scalars().all())


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

    async def run(self):
        last_month = await self.get_last_month_dayly_spent()
        last_week = await self.get_last_week_dayly_spent()
        current_month = await self.get_current_month_dayly_spent()
        current_week = await self.get_current_week_dayly_spent()
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
        variations = VariantionMetrics(
            from_last_week_daily=last_week_var_average,
            from_last_week_total=from_last_week_total,
            from_last_month_daily=from_last_month_daily,
            from_last_month_total=from_last_month_total,
        )
        return MetricsOverview(
            current_month=current_month_metric,
            last_month=last_month_metric,
            current_week=current_week_metric,
            last_week=last_week_metric,
            variation=variations,
        )

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        return ((current - before) / (before or 1)) * 100
