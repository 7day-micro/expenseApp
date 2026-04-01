import pytest
import pytest_asyncio

from src.auth.oauth2 import get_password_hash
from src.models import User
from src.domain.category.service import CategoryService
from src.exceptions import EntityNotFoundException
from src.domain.category.schemas import CategoryUpdateSchema


class TestCategoryService:
    @pytest_asyncio.fixture
    async def other_user(self, db_session, valid_user):
        other_user_payload = valid_user.model_copy(
            update={"username": "otheruser", "email": "otheruser@example.com"}
        )
        new_user = User(
            username=other_user_payload.username,
            email=other_user_payload.email,
            password_hash=get_password_hash(other_user_payload.password),
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
        assert result.id == category.id

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
    async def test_update_no_update_data(
        self, user_factory, db_session, category_factory
    ):
        service = CategoryService(db_session)

        user = await user_factory()
        category = await category_factory(user_id=user.uid)
        empty_update = CategoryUpdateSchema()

        await service.update(object_id=category.id, user_id=user.uid, data=empty_update)

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

    @pytest.mark.asyncio
    async def test_get_all_returns_only_user_categories(
        self, user, other_user, db_session, valid_category
    ):
        service = CategoryService(db_session)

        own_one = await service.create(data=valid_category, user_id=user.uid)
        own_two_payload = valid_category.model_copy(update={"name": "second-own"})
        own_two = await service.create(data=own_two_payload, user_id=user.uid)

        other_payload = valid_category.model_copy(update={"name": "other-user"})
        other = await service.create(data=other_payload, user_id=other_user.uid)

        user_categories = await service.get_all(user_id=user.uid)
        other_categories = await service.get_all(user_id=other_user.uid)

        assert len(user_categories) == 2
        assert {c.id for c in user_categories} == {own_one.id, own_two.id}
        assert all(c.user_id == user.uid for c in user_categories)

        assert len(other_categories) == 1
        assert other_categories[0].id == other.id
        assert all(c.user_id == other_user.uid for c in other_categories)

    @pytest.mark.asyncio
    async def test_get_all_returns_empty_list_for_user_with_no_categories(
        self, db_session
    ):
        service = CategoryService(db_session)
        from uuid import uuid4

        categories = await service.get_all(user_id=uuid4())
        assert categories == []
