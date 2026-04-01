from src.models import Budget
from src.errors.main import EntityNotFoundException, DatabaseException
from src.common.base_service import BaseService
from src.domain.budget.schemas import BudgetCreateSchema, BudgetSchema, BudgetUpdateSchema

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from typing import Any

class BudgetService(BaseService[Budget, BudgetCreateSchema, BudgetSchema ]):
    async def create(self, data: BudgetCreateSchema, user_id: UUID) -> Budget:
        budget = Budget(**data.model_dump(exclude={"user_id"}))
        budget.user_id = user_id

        self.db.add(budget)
        try:
            await self.db.commit()
            await self.db.refresh(budget)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="Budget",
                details={"user_id": str(user_id), "original_error": str(e)},
            ) from e

        return budget
    
    async def update(
        self, object_id: Any, data: BudgetUpdateSchema, user_id: UUID
    ) -> Budget:
        budget = await self.get_by_id(object_id, user_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(budget, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(budget)
            return budget
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="updating",
                entity_name="Budget",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e
    
    async def delete(self, object_id: Any, user_id: UUID) -> Budget:
        budget = await self.get_by_id(object_id, user_id)

        try:
            await self.db.delete(budget)
            await self.db.commit()
            return budget
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="deleting",
                entity_name="Budget",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            ) from e
    
    async def get_by_id(self, object_id: Any, user_id: UUID) -> Budget:
        statement = select(Budget).where(
            Budget.id == object_id, Budget.user_id == user_id
        )
        result = await self.db.execute(statement)
        budget = result.scalar_one_or_none()

        if not budget:
            raise EntityNotFoundException(entity_name="Budget", object_id=object_id)

        return budget
   
    async def get_all(self, user_id:UUID) -> list[Budget]:
        statement =  select(Budget).where(Budget.user_id == user_id)
        result = await self.db.execute(statement)
        return result.scalars().all()
        