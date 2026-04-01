from typing import List, Optional
from uuid import UUID

from src.domain.budget.schemas import BudgetCreateSchema, BudgetSchema
from src.exceptions import EntityNotFoundException
from src.models import Budget
from src.common import BaseService

from sqlalchemy import select


class BudgetService(BaseService[Budget, BudgetCreateSchema, BudgetSchema]):
    async def create(self, data: BudgetCreateSchema, user_id: UUID) -> Budget:
        new_budget = Budget(**data.model_dump())

        self.db.add(new_budget)
        await self.db.commit()

        return new_budget

    async def update(
        self, object_id: int, data: BudgetCreateSchema, user_id: UUID
    ) -> Optional[Budget]:
        budget = await self.get_by_id(object_id=object_id, user_id=user_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(budget, key, value)

        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    async def delete(self, object_id: int, user_id: UUID) -> Optional[Budget]:
        result = await self.get_by_id(object_id=object_id, user_id=user_id)

        await self.db.delete(result)
        await self.db.commit()
        return result

    async def get_by_id(self, object_id: int, user_id: UUID) -> Optional[Budget]:
        query = select(Budget).where(Budget.id == object_id, Budget.user_id == user_id)
        result = (await self.db.execute(query)).scalar_one_or_none()

        if result is None:
            raise EntityNotFoundException(object_id=object_id, entity_name="Budget")

        return result

    async def get_all(self, user_id: UUID) -> List[Budget]:
        query = select(Budget).where(Budget.user_id == user_id)
        results = await self.db.execute(query)
        return list(results.scalars().all())
