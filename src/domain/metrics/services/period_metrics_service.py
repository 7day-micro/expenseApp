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
        """
        Initialize the service with database session, user identifier, and optional custom range boundaries.
        
        Parameters:
            start_date (datetime.date | None): Optional inclusive start date for a custom metrics range; when provided, the service will use this instead of predefined period ranges.
            end_date (datetime.date | None): Optional exclusive end date for a custom metrics range; when provided, the service will use this instead of predefined period ranges.
        """
        self.session = session
        self.user_id = user_id
        self._start_date = start_date
        self._end_date = end_date

    def get_period(self, period: PERIOD_TIME) -> tuple[datetime.date, datetime.date]:
        """
        Return the start and end dates bounding a predefined reporting period relative to the current UTC date.
        
        Parameters:
            period (PERIOD_TIME): One of "curr_month", "curr_week", "last_month", or "last_week".
        
        Returns:
            tuple[start_date (datetime.date), end_date (datetime.date)]: 
                - For "curr_month": first day of the current month and tomorrow (end exclusive).
                - For "curr_week": first day of the current ISO week (Monday) and tomorrow (end exclusive).
                - For "last_month": first day of the previous month and first day of the current month.
                - For "last_week": first day of the previous ISO week and first day of the current ISO week.
        """
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
        """
        Assemble aggregated expense metrics for the given date range.
        
        Computes daily metrics, category and budget breakdowns, and derives totals and summaries for the period.
        average_daily is computed as grand total divided by the number of days in the range (uses 1 as the minimum denominator to avoid division by zero). projection is rounded to two decimal places. total_transaction is the sum of reported transactions across daily records.
        
        Parameters:
            start_date (datetime.date): Inclusive start date of the period.
            end_date (datetime.date): Exclusive end date of the period (the range is [start_date, end_date)).
        
        Returns:
            PeriodMetrics: Object containing:
                - daily: list of daily metric records for the range
                - total: grand total amount spent in the period
                - average_daily: average daily spending for the period
                - category_metrics: aggregated metrics grouped by category
                - projection: projected total for the period (quantized to 2 decimal places)
                - total_transaction: sum of transactions across daily records
                - budget_metrics: aggregated budget-related metrics for the period
        """

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

        budgets_metrics = await BudgetMetricsService(
            user_id=self.user_id,
            start_date=start_date,
            end_date=end_date,
            session=self.session,
        ).execute()

        result = PeriodMetrics(
            daily=days,
            total=grand_total,
            average_daily=average_daily_spending,
            category_metrics=category_metrics,
            # peak_spending=peak_spending_day,
            projection=projection,
            total_transaction=total_transaction,
            budget_metrics=budgets_metrics,
        )

        return result

    @staticmethod
    def get_past_vs_current(before: Decimal, current: Decimal):
        """
        Compute the percentage change from a previous value to a current value.
        
        Parameters:
        	before (Decimal): The baseline (previous) value to compare against.
        	current (Decimal): The current value.
        
        Returns:
        	Decimal: Percentage change where positive indicates an increase, negative indicates a decrease, and zero indicates no change.
        
        Raises:
        	ValueError: If `before` or `current` is None.
        
        Notes:
        	If `before` is zero, the baseline is treated as 1 to avoid division by zero.
        """
        if before is None or current is None:
            raise ValueError("cant")
        return ((current - before) / (before if before != 0 else 1)) * 100

    async def get_last_12_months(self):
        """
        Collect period metrics for monthly windows from two months ago through eleven months ago.
        
        Returns:
            months_metrics (dict[datetime.date, PeriodMetrics]): Mapping where each key is the first day of a past month (UTC) and each value is the metrics for the range from that month's first day up to the first day of the following month. The function covers months starting 2 through 11 months before the current month (inclusive).
        """
        today = datetime.datetime.now(tz=datetime.UTC).date().replace(day=1)
        months_metrics: dict[datetime.date, PeriodMetrics] = {}
        for i in range(2, 12):
            start = today - relativedelta(months=i)
            end = today - relativedelta(months=i - 1)

            res = await self.get_metrics(start, end)

            months_metrics[start] = res

        return months_metrics

    async def execute(self, with_range, last_year=True):
        """
        Assemble an overview of period metrics for current and previous month/week, optionally including a selected date range and last-12-months data.
        
        Parameters:
        	with_range (bool): If true and the instance has both `_start_date` and `_end_date` set, include daily metrics for that selected range.
        	last_year (bool): If true, include a mapping of the last 12 months' period metrics; if false, `last_12_months` will be an empty mapping.
        
        Returns:
        	MetricsOverview: Aggregated payload containing `current_month`, `last_month`, `current_week`, `last_week`, `variation`, `budgets_metrics`, `last_12_months`, and `selected_range`.
        """
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
