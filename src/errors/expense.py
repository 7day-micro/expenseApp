from src.errors.main import ExpenseException

class NoExpenseFound(ExpenseException):
    staus_code:int = 404
    error_code:str = 'no_expenses'
    message:str = 'No Expense Found'
