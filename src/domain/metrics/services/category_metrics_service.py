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
        self.user_id = user_id
        self._start_date = start_date
        self._end_date = end_date
        self.session = session

    @staticmethod
    def get_percentage_of_total(total: Decimal, part: Decimal):
        """Returns percentage contribution rounded to 2 decimal places."""
        return Decimal((part / max(1, total)) * 100).quantize(Decimal("0.00"))

    @property
    def statement(self):
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
        """Breaks period spend down by category with percentage share."""

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
