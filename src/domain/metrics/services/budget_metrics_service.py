import datetime
from decimal import Decimal

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
        """
        Initialize the BudgetMetricsService with a database session, target user, and analysis date range.

        Parameters:
            session (AsyncSession): Asynchronous database session used to execute queries.
            user_id: Identifier of the user whose budget metrics will be generated.
            start_date (datetime.date): Start of the reporting period; expected to be the first day of a month.
            end_date (datetime.date): End of the reporting period; used as the upper bound for query filtering.
        """
        self.session = session
        self.user_id = user_id
        self.start_date = start_date
        self.end_date = end_date

    @property
    def statement(self):
        """
        Builds a SQLAlchemy selectable that aggregates expense metrics per budget for the current month window.

        The selectable returns Budget plus computed columns:
        - `cat_id`: budget category id
        - `spent`: sum of Expense.amount for the window
        - `amount_limit`: Budget.amount_limit
        - `total_used`: sum of Expense.amount as a percentage of the budget limit
        - `average`: average Expense.amount

        Returns:
            sqlalchemy.sql.Select: A select() that joins Budget to Expense, filters expenses to the current month (bounded by the computed next month first day and `self.end_date`), and groups results by `Budget.id`.
        """

        return (
            select(
                Budget,
                Budget.category_id.label("cat_id"),  # category id
                func.sum(Expense.amount).label("spent"),  # sum of all expenses
                Budget.amount_limit,  # Budget target amount
                (func.sum(Expense.amount) / Budget.amount_limit * 100).label(
                    "total_used"
                ),  # total of use in percentage of all expenses agaisnt the amount limit
                (func.avg(Expense.amount)).label("average"),  # Average amount of spends
            )
            .join(
                Expense,
                and_(
                    Budget.category_id == Expense.category_id,
                ),
            )
            .where(
                Budget.month_year == self.start_date,
                Budget.user_id == self.user_id,
                Expense.transaction_date >= Budget.month_year,
                Expense.transaction_date < self.end_date,
            )
            .group_by(Budget.id)
        )

    async def execute(self):
        """
        Builds budget usage metrics for the relevant month grouped by budget/category.

        Returns:
            List[BudgetMetricSchema]: A list of budget metric objects for each returned budget row. Numeric aggregates (`total_used`, `average`, `spent`) are represented on the schema and default to `Decimal(0)` when the query returned NULL.
        """

        result = await self.session.execute(statement=self.statement)

        rows = result.all()

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
