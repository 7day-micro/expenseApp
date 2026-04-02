from typing import List, Optional
from uuid import UUID

from src.domain.budget.schemas import (
    BudgetCreateSchema,
    BudgetSchema,
    BudgetUpdateSchema,
)
from src.exceptions import EntityNotFoundException, DatabaseException
from src.models import Budget
from src.common import BaseService
from src.domain.category.service import CategoryService
from src.models import Category

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError


class BudgetService(BaseService[Budget, BudgetCreateSchema, BudgetSchema, BudgetUpdateSchema]): #fixed
    async def create(self, data: BudgetCreateSchema, user_id: UUID) -> Budget:
        """
        Create a new Budget from the provided creation schema and persist it to the database.

        Parameters:
            data (BudgetCreateSchema): Schema containing fields for the new Budget.
            user_id (UUID): Identifier of the user who owns the Budget.

        Returns:
            Budget: The persisted Budget instance.
        """
        new_budget = Budget(**data.model_dump(), user_id=user_id)
        try:
            self.db.add(new_budget)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="budget",
                details={"user_id": str(user_id), "original_error": str(e)},
            ) from e

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
        result = await self.db.get(Category, data.category_id)
        if not result:
            raise EntityNotFoundException(object_id=data.category_id, entity_name="Category")

        budget = await self.get_by_id(object_id=object_id, user_id=user_id)

        for key, value in data.model_dump(
            exclude_unset=True, exclude_none=True
        ).items():
            setattr(budget, key, value)

        try:
            await self.db.commit()
            await self.db.refresh(budget)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="update",
                entity_name="Budget",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            )
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

        try:
            await self.db.delete(result)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="delete",
                entity_name="Budget",
                details={
                    "object_id": object_id,
                    "user_id": str(user_id),
                    "original_error": str(e),
                },
            )
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
