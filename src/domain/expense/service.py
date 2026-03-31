from src.db.database import get_db
from src.models import User, Expense
from src.errors.expense import NoExpenseFound

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc



class expenseService:

    async def get_all_expenses(self, session:AsyncSession):
        statement =  select(Expense).order_by(desc(Expense.created_at))
            
        result = await session.execute(statement)
        if not result:
            raise NoExpenseFound
        expenses = result.scalars.all()
        return expenses
    
    async def get_user_expenses(self, session:AsyncSession, user:User):
        statement = select(Expense).where(Expense.user_id == user.uid)
        result = await session.execute(statement)
        


            



