from fastapi.exceptions import HTTPException

class AppException(Exception):
    staus_code: int  = 500
    error_code: str = "internal_error"
    message: str = "Internal Error Occured"

    def __init__(self, message:str = None, context:dict = None):
        self.message = message or self.message
        self.context = context or {}

        super().__init__(self.message)

class ExpenseException(AppException):
    pass
class AuthExeption(AppException):
    pass
class BudgetException(AppException):
    pass