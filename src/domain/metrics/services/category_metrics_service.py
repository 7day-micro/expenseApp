import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.category.schemas import CategorySchema
from src.domain.metrics.schemas import (
    CategoryMetricSchema,
)
from src.models import Category, Expense


class CategoryMetricService:
    def __init__(
        self,
        session: AsyncSession,
        user_id: UUID,
        start_date: datetime.date,
        end_date: datetime.date,
    ):
        """
        Initialize the service with an async database session, the target user's ID, and an inclusive date range.
        
        Parameters:
            session (AsyncSession): Async SQLAlchemy session used for executing queries.
            user_id (UUID): Identifier of the user whose category metrics will be computed.
            start_date (datetime.date): Inclusive start date for the metric range.
            end_date (datetime.date): Inclusive end date for the metric range.
        """
        self.user_id = user_id
        self._start_date = start_date
        self._end_date = end_date
        self.session = session

    @staticmethod
    def get_percentage_of_total(total: Decimal, part: Decimal):
        """
        Compute the percentage that `part` represents of `total`, rounded to two decimal places.
        
        Parameters:
            total (Decimal): The denominator total used to compute the percentage. If `total` is less than 1, the function treats it as 1 to avoid division by zero.
            part (Decimal): The portion value to express as a percentage of `total`.
        
        Returns:
            Decimal: The percentage value `(part / max(1, total)) * 100`, quantized to two decimal places.
        """
        return Decimal((part / max(1, total)) * 100).quantize(Decimal("0.00"))

    @property
    def statement(self):
        """
        Builds a SQLAlchemy selectable that computes expense metrics per category for the service's user and date range.
        
        The selectable yields rows with the following columns:
        - `cat_name`: category name
        - `total`: sum of `Expense.amount` for the category
        - `transaction_count`: number of `Expense` records for the category
        - `grand_total`: sum of `Expense.amount` across all matching expenses (same filters)
        - `Category`: the full `Category` entity
        
        The query filters to the service's `user_id`, excludes `Expense` rows with a null `category_id`, restricts `transaction_date` to the inclusive `[start_date, end_date]` range, and groups results by `Category.id`.
        """
        grand_total_st = (
            select(func.sum(Expense.amount))
            .where(
                Expense.transaction_date >= self._start_date,
                Expense.transaction_date <= self._end_date,
                Expense.user_id == self.user_id,
            )
            .scalar_subquery()
        )

        return (
            select(
                # MAKE sure updating this statement you update the DTO as well
                Category.name.label("cat_name"),
                func.sum(Expense.amount).label("total"),
                func.count(Expense.amount).label("transaction_count"),
                grand_total_st.label("grand_total"),
                Category,
            )
            .join(Category, Expense.category_id == Category.id)
            .where(
                Expense.user_id == self.user_id,
                Expense.category_id.isnot(None),
                Expense.transaction_date >= self._start_date,
                Expense.transaction_date <= self._end_date,
            )
            .group_by(Category.id)
        )

    async def execute(self) -> list[CategoryMetricSchema]:
        """
        Compute expense metrics per category for the service's user and date range.
        
        Executes the prepared query and converts each result row into a CategoryMetricSchema that includes the category's total amount, transaction count, validated category data, and percentage share of the grand total.
        
        Returns:
            list[CategoryMetricSchema]: A list of CategoryMetricSchema objects, one per category, containing `total`, `transaction_count`, `category`, and `percentage_of_total`.
        """

        result = await self.session.execute(statement=self.statement)

        rows = result.all()

        return [
            CategoryMetricSchema(
                total=row.total,
                transaction_count=row.transaction_count,
                category=CategorySchema.model_validate(row.Category),
                percentage_of_total=self.get_percentage_of_total(
                    row.grand_total, row.total
                ),
            )
            for row in rows
        ]
