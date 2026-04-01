from src.models import Expense
from src.errors.expense import (
    NoExpenseFound,
    ExpenseCreationDataBase,
    ExpenseDeletionDataBase,
)
from src.common.base_service import BaseService
from src.domain.expense.schemas import ExpenseCreateSchema, ExpenseResponseSchema

from sqlalchemy import select
from uuid import UUID
from typing import Optional, Any


class ExpenseService(BaseService[Expense, ExpenseCreateSchema, ExpenseResponseSchema]):
    async def create(self, data: ExpenseCreateSchema, user_id: UUID) -> Expense:

        expense_orm = Expense(**data.model_dump())
        expense_orm.user_id = user_id

        self.db.add(expense_orm)
        try:
            await self.db.commit()
            await self.db.refresh(expense_orm)
        except Exception:
            await self.db.rollback()
            raise ExpenseCreationDataBase()

        return expense_orm

    async def delete(self, object_id: Any, user_id: UUID) -> Optional[Expense]:

        expense_orm = await self.db.get(Expense, object_id)
        if not expense_orm:
            raise NoExpenseFound(message="No expense found with the provided ")

        try:
            await self.db.delete(expense_orm)
            await self.db.commit()
            return expense_orm
        except Exception:
            await self.db.rollback()
            raise ExpenseDeletionDataBase()

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Optional[Expense]:
        statement = select(Expense).where(
            Expense.id == object_id, Expense.user_id == user_id
        )
        result = await self.db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise NoExpenseFound(message="No expense found for the provided Expense ID")

        return expense

    async def get_all(self, user_uid: UUID):
        statement = select(Expense).where(Expense.user_id == user_uid)
        result = await self.db.execute(statement)
        expenses = result.scalars().all()
        if not expenses:
            raise NoExpenseFound(message="No Expense found for the user")
        return expenses

    # async def get_all_expenses(self) -> List[Expense]:
    #     statement =  select(Expense).order_by(desc(Expense.created_at))
    #     result = await self.db.execute(statement)
    #     expenses = result.scalars().all()

    #     if not expenses:
    #         raise NoExpenseFound()

    #     return expenses
