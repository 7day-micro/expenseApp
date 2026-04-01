import pytest
import pytest_asyncio

from src.auth.oauth2 import get_password_hash
from src.models import User
from src.domain.category.service import CategoryService
from src.errors.main import EntityNotFoundException


class TestCategoryService:
    @pytest_asyncio.fixture
    async def other_user(self, db_session):
        new_user = User(
            username="otheruser",
            email="otheruser@example.com",
            password_hash=get_password_hash("StrongePassWord123#"),
        )
        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)
        return new_user

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

        check = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert check is not None

        await service.delete(object_id=new_category.id, user_id=user.uid)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=new_category.id, user_id=user.uid)

    @pytest.mark.asyncio
    async def test_update(self, user, db_session, valid_category):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        result = await service.get_by_id(object_id=new_category.id, user_id=user.uid)

        assert result is not None

        updated_payload = valid_category.model_copy()
        updated_payload.name = "new name"

        await service.update(
            object_id=new_category.id, user_id=user.uid, data=updated_payload
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

    @pytest.mark.asyncio
    async def test_update_does_not_override_user_id(
        self, user, db_session, valid_category
    ):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        spoofed = valid_category.model_copy(
            update={"user_id": "00000000-0000-0000-0000-000000000000"}
        )
        updated = await service.update(
            object_id=new_category.id, user_id=user.uid, data=spoofed
        )

        assert str(updated.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_get_by_id_raises_for_other_user(self, category, db_session):
        service = CategoryService(db_session)
        from uuid import uuid4

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=category.id, user_id=uuid4())

    @pytest.mark.asyncio
    async def test_cross_user_access_raises_not_found(
        self, user, other_user, db_session, valid_category
    ):
        service = CategoryService(db_session)
        new_category = await service.create(data=valid_category, user_id=user.uid)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=new_category.id, user_id=other_user.uid)

        payload = valid_category.model_copy(update={"name": "blocked update"})
        with pytest.raises(EntityNotFoundException):
            await service.update(
                object_id=new_category.id,
                user_id=other_user.uid,
                data=payload,
            )

        with pytest.raises(EntityNotFoundException):
            await service.delete(object_id=new_category.id, user_id=other_user.uid)

    @pytest.mark.asyncio
    async def test_get_by_id_raises_for_nonexistent_category_id(self, user, db_session):
        service = CategoryService(db_session)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=999999, user_id=user.uid)
