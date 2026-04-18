import datetime
from decimal import Decimal
from uuid import UUID

from dateutil.relativedelta import relativedelta

from src.db.database import AsyncSession
from src.domain.metrics.schemas import (
    MetricsOverview,
    PeriodMetrics,
    VariationMetrics,
)
from src.domain.metrics.services.budget_metrics_service import BudgetMetricsService
from src.domain.metrics.services.category_metrics_service import CategoryMetricService
from src.domain.metrics.services.daily_metrics_service import DailyMetricsService
from src.domain.metrics.services.entities import PERIOD_TIME


class PeriodMetricsService:
    """Builds aggregated expense metrics for dashboard views."""

    def __init__(
        self,
        session: AsyncSession,
        user_id: UUID,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ):
        self.session = session
        self.user_id = user_id
        self._start_date = start_date
        self._end_date = end_date

    def get_period(self, period: PERIOD_TIME) -> tuple[datetime.date, datetime.date]:
        today = datetime.datetime.now(tz=datetime.UTC).date()
        tomorrow = today + relativedelta(days=1)
        # MONTH RELATED
        current_month_first_day = today.replace(day=1)
        past_month_first_day = current_month_first_day - relativedelta(months=1)
        # WEEK RELATED
        current_week_first_day = today - datetime.timedelta(days=today.isoweekday() - 1)
        past_week_first_day = current_week_first_day - datetime.timedelta(days=7)

        match period:
            case "curr_month":
                return (current_month_first_day, tomorrow)

            case "curr_week":
                return (current_week_first_day, tomorrow)

            case "last_month":
                return (past_month_first_day, current_month_first_day)

            case "last_week":
                return (past_week_first_day, current_week_first_day)

    async def get_metrics(self, start_date: datetime.date, end_date: datetime.date):
        """Computes dashboard metrics for a single period label."""

        days = await DailyMetricsService(
            self.user_id, start_date=start_date, end_date=end_date
        ).execute()

        num_days = (end_date - start_date).days

        grand_total = Decimal(sum(t.total_spent for t in days if t.total_spent))

        average_daily_spending = grand_total / max(1, num_days)

        projection = Decimal(average_daily_spending * num_days).quantize(
            Decimal("0.00")
        )
        total_transaction = sum(
            t.total_transactions for t in days if t.total_transactions
        )

        category_metrics = await CategoryMetricService(
            self.session, self.user_id, start_date, end_date
        ).execute()

        result = PeriodMetrics(
            daily=days,
            total=grand_total,
            average_daily=average_daily_spending,
            category_metrics=category_metrics,
            # peak_spending=peak_spending_day,
            projection=projection,
            total_transaction=total_transaction,
        )

        return result

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        """Percentage delta from a previous value to current value."""
        if before is None or current is None:
            raise ValueError("cant")
        return ((current - before) / (before if before != 0 else 1)) * 100

    async def get_last_12_months(self):
        today = datetime.datetime.now(tz=datetime.UTC).date().replace(day=1)
        months_metrics: dict[datetime.date, PeriodMetrics] = {}
        for i in range(2, 12):
            start = today - relativedelta(months=i)
            end = today - relativedelta(months=i - 1)

            res = await self.get_metrics(start, end)

            months_metrics[start] = res

        return months_metrics

    async def execute(self, with_range, last_year=True):
        """Generates the complete metrics overview payload."""
        last_month = await self.get_metrics(*self.get_period("last_month"))
        current_month = await self.get_metrics(*self.get_period("curr_month"))
        last_week = await self.get_metrics(*self.get_period("last_week"))
        current_week = await self.get_metrics(*self.get_period("curr_week"))

        # Compute week-over-week and month-over-month deltas.
        last_week_var_average = self.get_past_vs_current(
            last_week.average_daily,
            current_week.average_daily,
        )
        from_last_week_total = self.get_past_vs_current(
            last_week.total,
            current_week.total,
        )
        from_last_month_daily = self.get_past_vs_current(
            last_month.average_daily,
            current_month.average_daily,
        )
        from_last_month_total = self.get_past_vs_current(
            last_month.total,
            current_month.total,
        )
        variations = VariationMetrics(
            from_last_week_daily=last_week_var_average,
            from_last_week_total=from_last_week_total,
            from_last_month_daily=from_last_month_daily,
            from_last_month_total=from_last_month_total,
        )

        start, end = self.get_period("curr_month")
        budget_metric = await BudgetMetricsService(
            start_date=start,
            end_date=end,
            session=self.session,
            user_id=self.user_id,
        ).execute()

        last_12 = await self.get_last_12_months() if last_year else {}

        selected_range = []
        if with_range and self._start_date and self._end_date:
            selected_range = await DailyMetricsService(
                start_date=self._start_date,
                end_date=self._end_date,
                user_id=self.user_id,
            ).execute()

        return MetricsOverview(
            # ALWAYS INCLUDED
            current_month=current_month,
            last_month=last_month,
            current_week=current_week,
            last_week=last_week,
            variation=variations,
            budgets_metrics=budget_metric,
            last_12_months=last_12,
            # NEED REQUEST
            selected_range=selected_range,
        )
