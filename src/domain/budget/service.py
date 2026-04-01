from typing import List, Optional
from uuid import UUID

from src.domain.budget.schemas import (
    BudgetCreateSchema,
    BudgetSchema,
    BudgetUpdateSchema,
)
from src.exceptions import EntityNotFoundException
from src.models import Budget
from src.common import BaseService

from sqlalchemy import select


class BudgetService(BaseService[Budget, BudgetCreateSchema, BudgetSchema]):
    async def create(self, data: BudgetCreateSchema, user_id: UUID) -> Budget:
        """
        Create a new Budget from the provided creation schema and persist it to the database.
        
        Parameters:
            data (BudgetCreateSchema): Schema containing fields for the new Budget.
            user_id (UUID): Identifier of the user who owns the Budget.
        
        Returns:
            Budget: The persisted Budget instance.
    async def create(self, data: BudgetCreateSchema, user_id: UUID) -> Budget:
        new_budget = Budget(**data.model_dump(exclude={"user_id"}))
        new_budget.user_id = user_id

        self.db.add(new_budget)
        await self.db.commit()

        return new_budget

    # TODO : -> Make base service accept update schemas
    async def update(
        self, object_id: int, data: BudgetUpdateSchema, user_id: UUID
    ) -> Optional[Budget]:
        """
        Update the specified Budget with values provided in the update schema.
        
        Parameters:
            object_id (int): ID of the Budget to update.
            data (BudgetUpdateSchema): Partial update data; only explicitly set fields are applied.
            user_id (UUID): ID of the owner to scope the lookup.
        
        Returns:
            Budget: The updated Budget instance.
        
        Raises:
            EntityNotFoundException: If no Budget with the given id exists for the specified user.
        """
        budget = await self.get_by_id(object_id=object_id, user_id=user_id)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(budget, key, value)

        await self.db.commit()
        await self.db.refresh(budget)
        return budget

    async def delete(self, object_id: int, user_id: UUID) -> Optional[Budget]:
        """
        Delete a Budget belonging to the specified user.
        
        Parameters:
            object_id (int): ID of the Budget to delete.
            user_id (UUID): ID of the user who owns the Budget.
        
        Returns:
            Budget: The deleted Budget instance.
        
        Raises:
            EntityNotFoundException: If no Budget with the given `object_id` exists for `user_id`.
        """
        result = await self.get_by_id(object_id=object_id, user_id=user_id)

        await self.db.delete(result)
        await self.db.commit()
        return result

    async def get_by_id(self, object_id: int, user_id: UUID) -> Optional[Budget]:
        """
        Retrieve a Budget by its id scoped to a specific user.
        
        Parameters:
            object_id (int): The numeric id of the Budget to retrieve.
            user_id (UUID): The UUID of the user who must own the Budget.
        
        Returns:
            Budget: The matching Budget instance.
        
        Raises:
            EntityNotFoundException: If no Budget exists with the given id for the specified user.
        """
        query = select(Budget).where(Budget.id == object_id, Budget.user_id == user_id)
        result = (await self.db.execute(query)).scalar_one_or_none()

        if result is None:
            raise EntityNotFoundException(object_id=object_id, entity_name="Budget")

        return result

    async def get_all(self, user_id: UUID) -> List[Budget]:
        """
        Retrieve all Budget records belonging to the specified user.
        
        Parameters:
            user_id (UUID): Identifier of the user whose budgets should be returned.
        
        Returns:
            List[Budget]: A list of Budget instances owned by the user.
        """
        query = select(Budget).where(Budget.user_id == user_id)
        results = await self.db.execute(query)
        return list(results.scalars().all())
