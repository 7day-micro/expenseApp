from typing import List, Any, Optional
from uuid import UUID
from sqlalchemy import select

from src.common import BaseService
from src.common.base_service import Model
from src.models import Category
from src.domain.category.schemas import CategoryCreateSchema, CategorySchema


class CategoryService(BaseService[Category, CategoryCreateSchema, CategorySchema]):
    async def create(self, data: CategoryCreateSchema, user_id: UUID) -> Model:
        new_category = Category()

        new_category.name = data.name
        new_category.color_icon = data.color_icon
        new_category.user_id = user_id

        self.db.add(new_category)

        await self.db.commit()
        await self.db.refresh(new_category)
        return new_category

    async def update(
        self, object_id: Any, data: CategoryCreateSchema, user_id: UUID
    ) -> Optional[Category]:
        category = await self.get_by_id(object_id, user_id)

        if not category:
            return None

        for key, value in data.model_dump().items():
            setattr(category, key, value)

        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category

    async def delete(self, object_id: Any, user_id: UUID) -> Optional[Category]:
        category = await self.get_by_id(object_id, user_id)

        if not category:
            return None

        await self.db.delete(category)
        await self.db.commit()

        return category

    async def get_by_id(self, object_id: Any, user_id: UUID) -> Optional[Category]:
        return (
            await self.db.execute(
                select(Category)
                .where(Category.id == object_id)
                .where(Category.user_id == user_id)
            )
        ).scalar_one_or_none()

    async def get_all(self, user_id: UUID) -> List[Category]:
        query = await self.db.execute(
            select(Category).where(Category.user_id == user_id)
        )
        return list(query.scalars().all())
