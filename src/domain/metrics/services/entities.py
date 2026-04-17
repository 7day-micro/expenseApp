import datetime
from decimal import Decimal
from typing import Literal

PERIOD_TIME = Literal["curr_week", "curr_month", "last_week", "last_month"]


class TransactionRow:
    def __init__(self, transaction):
        self.total: Decimal = transaction.total
        self.date: datetime.datetime = transaction.date
        self.category_name: str = transaction.category_name
        self.id: int = transaction.id


class DailySummary:
    def __init__(self, date):
        self.date = date
        self.highest_expense: TransactionRow | None = None
        self.lowest_expense: TransactionRow | None = None
        self.transctions_count = 0
        self.total_spent = Decimal("0.00")

    def add_transaction(self, row):
        self.date = self.date
        self.total_spent += row.total
        self.transctions_count += 1

        if self.highest_expense is None or row.total > self.highest_expense.total:
            self.highest_expense = row

        if self.lowest_expense is None or row.total < self.lowest_expense.total:
            self.lowest_expense = row

    @property
    def transaction_average(self):
        return Decimal(self.total_spent / self.transctions_count).quantize(
            Decimal("0.00")
        )

    @property
    def is_anomaly(self):
        if self.highest_expense is None:
            return False

        return self.highest_expense.total > self.transaction_average * Decimal("1.50")
