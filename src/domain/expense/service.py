from src.models import Expense
from src.errors.main import EntityNotFoundException, DatabaseException
from src.common.base_service import BaseService
from src.domain.expense.schemas import ExpenseCreateSchema, ExpenseSchema

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from typing import Any


class ExpenseService(BaseService[Expense, ExpenseCreateSchema, ExpenseSchema]):
    async def create(self, data: ExpenseCreateSchema, user_id: UUID) -> Expense:
        expense = Expense(**data.model_dump(exclude={"user_id"}))
        expense.user_id = user_id

        self.db.add(expense)
        try:
            await self.db.commit()
            await self.db.refresh(expense)
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="Expense",
                details={"user_id": str(user_id), "original_error": str(e)},
            ) from e

        return expense

    async def update(
        self, object_id: Any, data: ExpenseCreateSchema, user_id: UUID
    ) -> Expense:
        expense = await self.get_by_id(object_id, user_id)
        for key, value in data.model_dump(exclude={"user_id"}).items():
            setattr(expense, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(expense)
            return expense
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="updating",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

    async def delete(self, object_id: Any, user_id: UUID) -> Expense:
        expense = await self.get_by_id(object_id, user_id)

        try:
            await self.db.delete(expense)
            await self.db.commit()
            return expense
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="deleting",
                entity_name="Expense",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Expense:
        statement = select(Expense).where(
            Expense.id == object_id, Expense.user_id == user_id
        )
        result = await self.db.execute(statement)
        expense = result.scalar_one_or_none()

        if not expense:
            raise EntityNotFoundException(entity_name="Expense", object_id=object_id)

        return expense

    async def get_all(self, user_id: UUID) -> list[Expense]:
        statement = select(Expense).where(Expense.user_id == user_id)
        result = await self.db.execute(statement)
        return result.scalars().all()
