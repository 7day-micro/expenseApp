import datetime
from decimal import Decimal

from dateutil import relativedelta
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.metrics.schemas import BudgetMetricSchema
from src.models import Budget, Expense


class BudgetMetricsService:
    """
    This class is responsible to generate metrics for budget

    """

    def __init__(
        self,
        session: AsyncSession,
        user_id,
        start_date: datetime.date,
        end_date: datetime.date,
    ) -> None:
        self.session = session
        self.user_id = user_id
        self.start_date = start_date  # always first day of month
        self.end_date = end_date

    @property
    def statement(self):
        today = datetime.datetime.now(tz=datetime.UTC).date()

        first_month_day = today.replace(day=1)
        next_month_first_day = first_month_day + relativedelta.relativedelta(months=1)
        return (
            select(
                Budget,
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
                    Expense.transaction_date <= self.end_date,
                ),
            )
            .where(
                Budget.month_year < next_month_first_day,
                Budget.month_year == first_month_day,
            )
            .group_by(Budget.id)
        )

    async def execute(self):
        """Builds current-month budget usage metrics by category."""

        rows = await self.session.execute(statement=self.statement)

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
