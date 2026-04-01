from src.errors.main import ExpenseException

class NoExpenseFound(ExpenseException):
    staus_code:int = 404
    error_code:str = 'no_expenses'
    message:str = 'No Expense Found'

class ExpenseCreationDataBase(ExpenseException):
    status_code:int  = 500
    error_code:str = 'db_fail_expense'
    message:str = 'Error while committing user to the db'

class ExpenseDeletionDataBase(ExpenseException):
    status_code:int  = 500
    error_code:str = 'db_fail_expense'
    message:str = 'Error while deleting user from the db'
 