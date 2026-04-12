import calendar
import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, and_
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
from src.domain.expense.schemas import VariationMetrics, MetricsOverview
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Category
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
        page: int = 1,
        limit: int = 20,
        date_filter: datetime.date | None = None,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
        min_value: Decimal | None = None,
        max_value: Decimal | None = None,
    ) -> PaginatedResponseSchema:
        if limit < 1:
            raise
        statement = select(Expense).where(
            Expense.user_id == user_id
        )  # statement for extraction

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

        """ count_statement = select(func.count()).select_from(statement.subquery()) """
        """ total_count = await self.db.execute(count_statement).scalar() or 0 """

        max_limit = 50

        safe_page = max(1, page)  # Sanitize for positive value
        safe_limit = min(limit, max_limit)  # ensure limit is positive and at most 50.

        statement = statement.order_by(
            Expense.transaction_date.desc(), Expense.id.desc()
        )

        statement = statement.offset((safe_page - 1) * safe_limit).limit(
            safe_limit
        )  # Subtracting 1 as default page is 1 which is first page with no offset

        result = await self.db.execute(statement)
        return list(result.scalars().all())


class ExpenseMetricGenerator:
    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.uid = user_id

    @property
    def last_month_range_statement(self):
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
                func.count("*").label("count"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(Expense.user_id == self.uid, range_statement)
            .group_by(func.date(Expense.transaction_date))
            .order_by(func.date(Expense.transaction_date))
        )

    @staticmethod
    def get_percentage_of_total(total: Decimal, part: Decimal):
        return Decimal((part / max(1, total)) * 100).quantize(Decimal("0.00"))

    async def get_period_metrics(self, time_range_stmt):
        stmt = self.get_statement(time_range_stmt)

        result = await self.db.execute(statement=stmt)

        rows = result.all()
        grand_total = rows[0].grand_total if rows else Decimal(0)
        days = {row.day: DailyMetrics(total=row.total, count=row.count) for row in rows}
        average_daily_spending = (
            grand_total / datetime.datetime.now(tz=datetime.UTC).date().isoweekday()
        )

        category_metrics = await self.get_category_metrics(
            time_range_stmt=self.current_month_range_statement
        )

        return PeriodMetrics(
            daily=days,
            total=grand_total,
            average_daily=average_daily_spending,
            category_metrics=category_metrics,
        )

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        return ((current - before) / (before if before != 0 else 1)) * 100

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

    async def run(self):
        async with SessionLocal.begin() as session:
            last_month = await self.get_period_metrics(self.last_month_range_statement)
            last_week = await self.get_period_metrics(self.last_week_range_statement)
            current_month = await self.get_period_metrics(
                self.current_month_range_statement
            )
            current_week = await self.get_period_metrics(
                self.current_week_range_statement
            )

            ## VS ============

            last_week_var_average = ExpenseMetricGenerator.get_past_vs_current(
                last_week.average_daily,
                current_week.average_daily,
            )

            from_last_week_total = ExpenseMetricGenerator.get_past_vs_current(
                last_week.total,
                current_week.total,
            )

            from_last_month_daily = ExpenseMetricGenerator.get_past_vs_current(
                last_month.average_daily,
                current_month.average_daily,
            )
            from_last_month_total = ExpenseMetricGenerator.get_past_vs_current(
                last_month.total,
                current_month.total,
            )

            variations = VariationMetrics(
                from_last_week_daily=last_week_var_average,
                from_last_week_total=from_last_week_total,
                from_last_month_daily=from_last_month_daily,
                from_last_month_total=from_last_month_total,
            )

            return MetricsOverview(
                current_month=current_month,
                last_month=last_month,
                current_week=current_month,
                last_week=last_week,
                variation=variations,
            )
