from uuid import uuid4

import pytest
import pytest_asyncio

from src.domain.category.schemas import CategorySchema, CategoryUpdateSchema


CATEGORY_BASE_PATH = "/categories"


@pytest.fixture
def category_payload(valid_category):
    return valid_category.model_copy()


@pytest.fixture
def category_update_payload():
    return CategoryUpdateSchema(name="Updated category", color_icon="updated-icon")


@pytest_asyncio.fixture
async def create_category_request(authenticated_client, category_payload):
    async def _factory(payload=None, client=None):
        payload = payload or category_payload.model_copy()
        client = client or authenticated_client
        return await client.post(
            f"{CATEGORY_BASE_PATH}/", data=payload.model_dump_json()
        )

    return _factory


class TestCategoryRoutes:
    @pytest.mark.asyncio
    async def test_create_category(self, create_category_request, user):
        response = await create_category_request()

        assert response.status_code == 201
        data = CategorySchema.model_validate(response.json())

        assert data.id is not None
        assert str(data.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_create_category_invalid_payload(
        self, create_category_request, category_payload
    ):
        invalid_payload = category_payload.model_copy()
        invalid_payload.name = None

        response = await create_category_request(payload=invalid_payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_category_unauthenticated(
        self, async_client, category_payload
    ):
        response = await async_client.post(
            f"{CATEGORY_BASE_PATH}/", data=category_payload.model_dump_json()
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_categories_route(
        self, authenticated_client, category_factory, user
    ):
        for _ in range(3):
            await category_factory(user_id=user.uid)

        response = await authenticated_client.get(f"{CATEGORY_BASE_PATH}/")

        assert response.status_code == 200
        data = list(map(CategorySchema.model_validate, response.json()))

        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_categories_unauthenticated(self, async_client):
        response = await async_client.get(f"{CATEGORY_BASE_PATH}/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_only_own_categories(
        self, authenticated_client, category_factory, user, second_user
    ):
        for _ in range(20):
            await category_factory(user_id=user.uid)
            await category_factory(user_id=second_user.uid)

        response = await authenticated_client.get(f"{CATEGORY_BASE_PATH}/")

        assert response.status_code == 200
        data = list(map(CategorySchema.model_validate, response.json()))

        assert len(data) == 20
        assert all(str(category.user_id) == str(user.uid) for category in data)

    @pytest.mark.asyncio
    async def test_get_category_by_id_route(
        self, create_category_request, authenticated_client
    ):
        created = await create_category_request()
        assert created.status_code == 201
        created_category = CategorySchema.model_validate(created.json())

        response = await authenticated_client.get(
            f"{CATEGORY_BASE_PATH}/{created_category.id}"
        )

        assert response.status_code == 200

        category_from_response = CategorySchema.model_validate(response.json())
        assert category_from_response.id == created_category.id

    @pytest.mark.asyncio
    async def test_get_category_by_id_unauthenticated(self, async_client):
        response = await async_client.get(f"{CATEGORY_BASE_PATH}/1")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_category_by_id_non_existent(self, authenticated_client):
        response = await authenticated_client.get(f"{CATEGORY_BASE_PATH}/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_route(
        self,
        create_category_request,
        authenticated_client,
        category_update_payload,
        user,
    ):
        created = await create_category_request()
        assert created.status_code == 201
        created_category = CategorySchema.model_validate(created.json())

        update_response = await authenticated_client.patch(
            f"{CATEGORY_BASE_PATH}/{created_category.id}",
            data=category_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 200

        updated = CategorySchema.model_validate(update_response.json())
        assert updated.id == created_category.id
        assert updated.name == category_update_payload.name
        assert updated.color_icon == category_update_payload.color_icon
        assert str(updated.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_user_cannot_update_other_user_category(
        self,
        authenticated_client,
        category_factory,
        second_user,
        category_update_payload,
    ):
        other_user_category = await category_factory(user_id=second_user.uid)

        update_response = await authenticated_client.patch(
            f"{CATEGORY_BASE_PATH}/{other_user_category.id}",
            data=category_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_category_unauthenticated(
        self, async_client, category_factory, user, category_update_payload
    ):
        category = await category_factory(user_id=user.uid)

        update_response = await async_client.patch(
            f"{CATEGORY_BASE_PATH}/{category.id}",
            data=category_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_category_does_not_override_user_id(
        self, create_category_request, authenticated_client, category_payload, user
    ):
        created = await create_category_request()
        assert created.status_code == 201
        created_category = CategorySchema.model_validate(created.json())

        spoofed_payload = category_payload.model_copy(
            update={"name": "Spoofed", "user_id": uuid4()}
        )
        update_response = await authenticated_client.patch(
            f"{CATEGORY_BASE_PATH}/{created_category.id}",
            data=spoofed_payload.model_dump_json(),
        )

        assert update_response.status_code == 200
        updated = CategorySchema.model_validate(update_response.json())
        assert str(updated.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_delete_category_route(
        self, create_category_request, authenticated_client
    ):
        created = await create_category_request()
        assert created.status_code == 201
        category_id = created.json()["id"]

        delete_response = await authenticated_client.delete(
            f"{CATEGORY_BASE_PATH}/{category_id}"
        )
        assert delete_response.status_code == 200

        get_response = await authenticated_client.get(
            f"{CATEGORY_BASE_PATH}/{category_id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_non_existent_category(self, authenticated_client):
        response = await authenticated_client.delete(f"{CATEGORY_BASE_PATH}/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_category_unauthenticated(
        self, create_category_request, authenticated_client
    ):
        created = await create_category_request()
        assert created.status_code == 201
        category_id = created.json()["id"]

        authenticated_client.headers.pop("Authorization", None)
        response = await authenticated_client.delete(
            f"{CATEGORY_BASE_PATH}/{category_id}"
        )

        assert response.status_code == 401
