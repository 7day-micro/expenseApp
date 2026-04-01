import pytest

from src.domain.category.service import CategoryService


class TestCategoryService:
    @pytest.mark.asyncio
    async def test_create_category(self, user, db_session, valid_category):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        assert new_category is not None
        assert new_category.name == valid_category.name
        assert new_category.color_icon == valid_category.color_icon
        assert new_category.user_id == user.uid

    @pytest.mark.asyncio
    async def test_delete_category(self, user, db_session, valid_category):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        assert new_category is not None
        await db_session.commit()

        check = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert check is not None

        await service.delete(object_id=new_category.id, user_id=user.uid)

        result = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert result is None

    @pytest.mark.asyncio
    async def test_update(self, user, db_session, valid_category):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        result = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert result is not None

        valid_category.name = "new name"

        await service.update(
            object_id=new_category.id, user_id=user.uid, data=valid_category
        )

        result = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert result is not None

        assert result.name == "new name"

    @pytest.mark.asyncio
    async def test_get_by_id(self, category, db_session, user):
        service = CategoryService(db_session)

        result = await service.get_by_id(object_id=category.id, user_id=user.uid)

        assert result is not None
        assert result.name == category.name
        assert result.color_icon == category.color_icon
        assert result.user_id == user.uid
        assert result == category
