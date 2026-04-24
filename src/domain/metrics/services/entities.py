import datetime
from decimal import Decimal
from typing import Literal

PERIOD_TIME = Literal["curr_week", "curr_month", "last_week", "last_month"]


class TransactionRow:
    def __init__(self, transaction):
        """
        Initialize a TransactionRow wrapper by copying selected attributes from the given transaction.
        
        Parameters:
            transaction: An object providing `total` (Decimal), `date` (datetime.datetime), `category_name` (str), and `id` (int); these attributes are copied onto the new instance as `total`, `date`, `category_name`, and `id`.
        """
        self.total: Decimal = transaction.total
        self.date: datetime.datetime = transaction.date
        self.category_name: str = transaction.category_name
        self.id: int = transaction.id


class DailySummary:
    def __init__(self, date):
        """
        Initialize a DailySummary for the given date and set aggregation defaults.
        
        Parameters:
            date (datetime.date | datetime.datetime): The day this summary represents.
        
        Initializes:
            highest_expense (TransactionRow | None): Highest expense seen for the day, initially None.
            lowest_expense (TransactionRow | None): Lowest expense seen for the day, initially None.
            transctions_count (int): Number of transactions aggregated (misspelled attribute name), initially 0.
            total_spent (Decimal): Total spent for the day, initially Decimal("0.00").
        """
        self.date = date
        self.highest_expense: TransactionRow | None = None
        self.lowest_expense: TransactionRow | None = None
        self.transctions_count = 0
        self.total_spent = Decimal("0.00")

    def add_transaction(self, row):
        """
        Aggregate a transaction row into the daily summary, updating totals, count, and min/max expense records.
        
        Parameters:
            row (TransactionRow): Transaction to include; its `total`, `date`, `category_name`, and `id` are used to update the summary.
        
        """
        self.date = self.date
        self.total_spent += row.total
        self.transctions_count += 1

        if self.highest_expense is None or row.total > self.highest_expense.total:
            self.highest_expense = row

        if self.lowest_expense is None or row.total < self.lowest_expense.total:
            self.lowest_expense = row

    @property
    def transaction_average(self):
        """
        Compute the average transaction amount for the day.
        
        Returns:
            Decimal: Average expense per transaction, quantized to two decimal places.
        
        Raises:
            ZeroDivisionError: If there are no transactions (transctions_count is zero).
        """
        return Decimal(self.total_spent / self.transctions_count).quantize(
            Decimal("0.00")
        )

    @property
    def is_anomaly(self):
        """
        Determine whether the day's highest expense qualifies as an anomaly.
        
        Returns:
            `true` if the highest expense is greater than 1.5 × the day's transaction average, `false` otherwise. If there is no highest expense (no transactions), returns `false`.
        """
        if self.highest_expense is None:
            return False

        return self.highest_expense.total > self.transaction_average * Decimal("1.50")
