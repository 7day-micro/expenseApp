import datetime
from decimal import Decimal
from math import ceil
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.common.base_service import BaseService
from src.domain.category.schemas import CategorySchema
from src.domain.category.service import CategoryService
from src.domain.expense.schemas import (
    BudgetMetricSchema,
    CategoryMetricSchema,
    DailyMetrics,
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    MetaSchema,
    MetricsOverview,
    PaginatedResponseSchema,
    PeakSpendingDay,
    PeriodMetrics,
    VariationMetrics,
)
from src.exceptions import DatabaseException, EntityNotFoundException
from src.models import Budget, Category, Expense

PERIOD_TIME = Literal["curr_week", "curr_month", "last_week", "last_month"]


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
        statement = (
            select(Expense)
            .options(selectinload(Expense.category))
            .where(Expense.id == object_id, Expense.user_id == user_id)
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
        statement = (
            select(Expense)
            .options(
                selectinload(Expense.category)
            )  # Loading the categories to avoid N+1
            .where(Expense.user_id == user_id)
        )

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

        count_statement = select(func.count()).select_from(statement.subquery())

        total_count = (
            (await self.db.execute(count_statement)).scalar() or 0
        )  # Return 0 instead of None if no such expense. Otherwise return the count

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
        result_list = list(result.scalars().all())

        meta = MetaSchema(
            total=total_count,
            count=len(result_list),
            page=safe_page,
            total_pages=ceil(total_count / safe_limit),
        )
        return PaginatedResponseSchema(data=result_list, meta=meta)


class ExpenseMetricGenerator:
    """Builds aggregated expense metrics for dashboard views."""

    def __init__(self, db: AsyncSession, user_id: UUID):
        self.db = db
        self.uid = user_id

    @property
    def last_month_range_statement(self):
        """SQL filter for the full previous month."""
        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )

        current_month_first_day = today.replace(day=1).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )
        passed_month_last_day = current_month_first_day - datetime.timedelta(days=1)
        passed_month_first_day = passed_month_last_day.replace(day=1)

        return and_(
            Expense.transaction_date >= passed_month_first_day,
            Expense.transaction_date < current_month_first_day,
        )

    @property
    def current_month_range_statement(self):
        """SQL filter from current month start until today (inclusive)."""
        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )
        tomorrow = today + datetime.timedelta(days=1)

        current_month_first_day = today.replace(day=1)

        return and_(
            Expense.transaction_date >= current_month_first_day,
            Expense.transaction_date < tomorrow,
        )

    @property
    def last_week_range_statement(self):
        """SQL filter for the previous ISO week (Mon-Sun window)."""
        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )
        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)
        passed_week_first_day = current_week_first_day - datetime.timedelta(days=7)

        return and_(
            Expense.transaction_date >= passed_week_first_day,
            Expense.transaction_date < current_week_first_day,
        )

    @property
    def current_week_range_statement(self):
        """SQL filter from current ISO week start until today (inclusive)."""
        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )
        tomorrow = today + datetime.timedelta(days=1)

        today_weekday = today.isoweekday()

        current_week_first_day = today - datetime.timedelta(days=today_weekday - 1)

        return and_(
            Expense.transaction_date >= current_week_first_day,
            Expense.transaction_date < tomorrow,
        )

    def get_statement(self, range_statement):
        """Daily aggregation query for a given period."""
        return (
            select(
                func.sum(Expense.amount).label("total"),
                func.count("*").label("count"),
                func.sum(func.sum(Expense.amount)).over().label("grand_total"),
                func.sum(func.count("*")).over().label("total_transactions"),
                func.date(Expense.transaction_date).label("day"),
            )
            .where(Expense.user_id == self.uid, range_statement)
            .group_by(Expense.transaction_date)
            .order_by(Expense.transaction_date)
        )

    @staticmethod
    def get_percentage_of_total(total: Decimal, part: Decimal):
        """Returns percentage contribution rounded to 2 decimal places."""
        return Decimal((part / max(1, total)) * 100).quantize(Decimal("0.00"))

    async def get_period_metrics(self, period: PERIOD_TIME):
        """Computes dashboard metrics for a single period label."""

        # Resolve period filter and number of elapsed days for average calculations.
        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )
        time_range_stmt = ""
        num_days = 0
        match period:
            case "curr_month":
                time_range_stmt = self.current_month_range_statement
                num_days = today.day
            case "curr_week":
                time_range_stmt = self.current_week_range_statement
                num_days = today.isoweekday()
            case "last_month":
                time_range_stmt = self.last_month_range_statement
                num_days = (today.replace(day=1) - datetime.timedelta(days=1)).day
            case "last_week":
                time_range_stmt = self.last_week_range_statement
                num_days = 7
            case _:
                raise ValueError("metrics need a period")

        # Execute daily aggregation rows for the selected period.
        stmt = self.get_statement(time_range_stmt)
        result = await self.db.execute(statement=stmt)

        # Materialize the result set for downstream transformations.
        rows = result.all()

        # Total amount for the period; defaults to 0 when there are no rows.
        grand_total = rows[0].grand_total if rows else Decimal(0)

        # Build a day-indexed map only for days with transactions.
        days = {row.day: DailyMetrics(total=row.total, count=row.count) for row in rows}

        # Average uses elapsed days, so days with no transactions are included.
        average_daily_spending = Decimal(grand_total / max(1, num_days)).quantize(
            Decimal("0.00")
        )

        # Keep transaction count aligned with the aggregate row payload.
        total_transaction = rows[0].total_transactions if grand_total else 0

        category_metrics = await self.get_category_metrics(
            time_range_stmt=time_range_stmt
        )

        peak_day = max(days.items(), key=lambda x: x[1].total) if days else None

        peak_spending_day = (
            PeakSpendingDay(
                count=peak_day[1].count, date=peak_day[0], total=peak_day[1].total
            )
            if peak_day
            else None
        )

        days_for_projection = 0
        match period:
            case "curr_month":
                # Project current pace over the full month length.
                first_day_next_month = (today + datetime.timedelta(days=32)).replace(
                    day=1
                )
                curr_month_day_count = (
                    first_day_next_month - datetime.timedelta(days=1)
                ).day
                days_for_projection = curr_month_day_count
            case "curr_week":
                # Project current pace over a full week.
                days_for_projection = 7

        projection = average_daily_spending * days_for_projection

        return PeriodMetrics(
            daily=days,
            total=grand_total,
            average_daily=average_daily_spending,
            category_metrics=category_metrics,
            peak_spending=peak_spending_day,
            projection=projection,
            total_transaction=total_transaction,
        )

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        """Percentage delta from a previous value to current value."""
        if before is None or current is None:
            raise ValueError("cant")
        return ((current - before) / (before if before != 0 else 1)) * 100

    async def get_category_metrics(self, time_range_stmt) -> list[CategoryMetricSchema]:
        """Breaks period spend down by category with percentage share."""
        grand_total_st = (
            select(func.sum(Expense.amount))
            .where(time_range_stmt, Expense.user_id == self.uid)
            .scalar_subquery()
        )

        statement = (
            select(
                Category.name.label("cat_name"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.amount).label("transaction_count"),
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
                transaction_count=row.transaction_count,
                category=CategorySchema.model_validate(row.Category),
                percentage_of_total=ExpenseMetricGenerator.get_percentage_of_total(
                    row.grand_total, row.total
                ),
            )
            for row in rows
        ]

    async def get_budgte_metrics(self):
        """Builds current-month budget usage metrics by category."""

        today = datetime.datetime.now(tz=datetime.UTC).replace(
            hour=0,
            microsecond=0,
            minute=0,
            second=0,
        )

        first_month_day = today.replace(day=1)
        next_month_first_day = (today + datetime.timedelta(days=32)).replace(day=1)

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
                    Expense.transaction_date < next_month_first_day,
                ),
            )
            .where(
                Budget.month_year <= next_month_first_day,
                Budget.month_year >= first_month_day,
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

    async def run(self):
        """Generates the complete metrics overview payload."""
        last_month = await self.get_period_metrics("last_month")
        current_month = await self.get_period_metrics("curr_month")
        last_week = await self.get_period_metrics("last_week")
        current_week = await self.get_period_metrics("curr_week")
        # Compute week-over-week and month-over-month deltas.
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
        budget_metric = await self.get_budgte_metrics()
        return MetricsOverview(
            current_month=current_month,
            last_month=last_month,
            current_week=current_week,
            last_week=last_week,
            variation=variations,
            budgets_metrics=budget_metric,
        )
