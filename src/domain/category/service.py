from typing import List, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.common import BaseService
from src.common.base_service import Model
from src.models import Category
from src.domain.category.schemas import CategoryCreateSchema, CategorySchema
from src.exceptions import EntityNotFoundException, DatabaseException


class CategoryService(BaseService[Category, CategoryCreateSchema, CategorySchema]):
    async def create(self, data: CategoryCreateSchema, user_id: UUID) -> Model:
        new_category = Category()
        new_category.name = data.name
        new_category.color_icon = data.color_icon
        new_category.user_id = user_id

        self.db.add(new_category)
        try:
            await self.db.commit()
            await self.db.refresh(new_category)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="creating",
                entity_name="Category",
                details={"user_id": str(user_id)},
            ) from e
        return new_category

    async def update(
        self, object_id: Any, data: CategoryCreateSchema, user_id: UUID
    ) -> Category:
        category = await self.get_by_id(object_id, user_id)
        for key, value in data.model_dump(exclude={"user_id"}).items():
            setattr(category, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(category)
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="updating",
                entity_name="Category",
                details={"object_id": object_id, "user_id": str(user_id)},
            ) from e
        return category

    async def delete(self, object_id: Any, user_id: UUID) -> Category:
        category = await self.get_by_id(object_id, user_id)
        try:
            await self.db.delete(category)
            await self.db.commit()
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise DatabaseException(
                operation="deleting",
                entity_name="Category",
                details={"object_id": object_id, "user_id": str(user_id)},
            ) from e

        return category

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Category:
        category = (
            await self.db.execute(
                select(Category)
                .where(Category.id == object_id)
                .where(Category.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not category:
            raise EntityNotFoundException(entity_name="Category", object_id=object_id)
        return category

    async def get_all(self, user_id: UUID) -> List[Category]:
        query = await self.db.execute(
            select(Category).where(Category.user_id == user_id)
        )
        return list(query.scalars().all())
