import datetime
import uuid

from sqlalchemy import func, select

from src.db.database import SessionLocal
from src.domain.expense.schemas import (
    SimplifiedExpenseSchema,
)
from src.domain.metrics.schemas import (
    DailyMetric,
)
from src.domain.metrics.services.entities import DailySummary, TransactionRow
from src.models import Category, Expense


class DailyMetricsService:
    def __init__(
        self, user_id: uuid.UUID, start_date: datetime.date, end_date: datetime.date
    ):
        self.user_id = user_id
        self._start_date = start_date
        self._end_date = end_date

    @property
    def statement(self):
        return (
            # Make sure when updating this select, changes reflect on Transaction Class
            select(
                Expense.id,
                Expense.amount.label("total"),
                func.date(Expense.transaction_date).label("date"),
                Category.name.label("category_name"),
            )
            .outerjoin(Category, Category.id == Expense.category_id)
            .where(
                Expense.transaction_date >= self._start_date,
                Expense.transaction_date <= self._end_date,
                Expense.user_id == self.user_id,
            )
            .order_by(func.date(Expense.transaction_date))
        )

    async def execute(self) -> list[DailyMetric]:

        async with SessionLocal.begin() as session:
            # Getting rows aka transactions
            rows = (await session.execute(self.statement)).all()

            # Casting to python object
            transactions = [TransactionRow(row) for row in rows]

            summary_of_days: dict[datetime.date, DailySummary] = {}

            for transaction in transactions:
                if summary_of_days.get(transaction.date):
                    summary_of_days[transaction.date].add_transaction(transaction)
                    continue
                summary_of_days[transaction.date] = DailySummary(date=transaction.date)

            return self._formart_response(summary_of_days=summary_of_days)

    def _formart_response(self, summary_of_days: dict[datetime.date, DailySummary]):
        daily_metrics = []

        for day, info in sorted(summary_of_days.items()):
            lowest_expense = info.lowest_expense
            highest_expense = info.highest_expense

            if lowest_expense is None or highest_expense is None:
                return []

            daily_metrics.append(
                DailyMetric(
                    date=day,
                    total_spent=info.total_spent,
                    total_transactions=info.transctions_count,
                    transaction_average=info.transaction_average,
                    is_anomaly=info.is_anomaly,
                    max=SimplifiedExpenseSchema(
                        amount=highest_expense.total,
                        id=highest_expense.id,
                        category_name=highest_expense.category_name,
                    ),
                    min=SimplifiedExpenseSchema(
                        id=lowest_expense.id,
                        amount=lowest_expense.total,
                        category_name=lowest_expense.category_name,
                    ),
                )
            )

        return daily_metrics
