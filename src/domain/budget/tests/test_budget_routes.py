from datetime import timedelta

import pytest
import pytest_asyncio

from src.domain.budget.schemas import BudgetSchema, BudgetUpdateSchema


BUDGET_BASE_PATH = "/budgets"


@pytest.fixture
def budget_payload(valid_budget_payload):
    return valid_budget_payload.model_copy()


@pytest.fixture
def budget_update_payload(valid_budget_payload):
    return BudgetUpdateSchema(
        amount_limit=valid_budget_payload.amount_limit + 10,
        month_year=valid_budget_payload.month_year + timedelta(days=30),
    )


@pytest_asyncio.fixture
async def create_budget_request(authenticated_client, budget_payload):
    async def _factory(payload=None, client=None):
        payload = payload or budget_payload.model_copy()
        client = client or authenticated_client
        return await client.post(f"{BUDGET_BASE_PATH}/", data=payload.model_dump_json())

    return _factory


class TestBudgetRoutes:
    @pytest.mark.asyncio
    async def test_create_budget(self, create_budget_request, user, budget_payload):
        response = await create_budget_request()

        assert response.status_code == 201
        data = BudgetSchema.model_validate(response.json())

        assert data.id is not None
        assert str(data.user_id) == str(user.uid)
        assert data.category_id == budget_payload.category_id

    @pytest.mark.asyncio
    async def test_create_budget_invalid_payload(
        self, create_budget_request, budget_payload
    ):
        invalid_payload = budget_payload.model_copy()
        invalid_payload.amount_limit = None

        response = await create_budget_request(payload=invalid_payload)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_budget_unauthenticated(self, async_client, budget_payload):
        response = await async_client.post(
            f"{BUDGET_BASE_PATH}/", data=budget_payload.model_dump_json()
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_budgets_route(self, authenticated_client, budget_factory, user):
        for _ in range(3):
            await budget_factory(user_id=user.uid)

        response = await authenticated_client.get(f"{BUDGET_BASE_PATH}/")

        assert response.status_code == 200
        data = list(map(BudgetSchema.model_validate, response.json()))

        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_budgets_unauthenticated(self, async_client):
        response = await async_client.get(f"{BUDGET_BASE_PATH}/")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_only_own_budgets(
        self, authenticated_client, budget_factory, user, second_user
    ):
        for _ in range(10):
            await budget_factory(user_id=user.uid)
            await budget_factory(user_id=second_user.uid)

        response = await authenticated_client.get(f"{BUDGET_BASE_PATH}/")

        assert response.status_code == 200
        data = list(map(BudgetSchema.model_validate, response.json()))

        assert len(data) == 10
        assert all(str(budget.user_id) == str(user.uid) for budget in data)

    @pytest.mark.asyncio
    async def test_get_budget_by_id_route(
        self, create_budget_request, authenticated_client
    ):
        created = await create_budget_request()
        assert created.status_code == 201
        created_budget = BudgetSchema.model_validate(created.json())

        response = await authenticated_client.get(
            f"{BUDGET_BASE_PATH}/{created_budget.id}"
        )

        assert response.status_code == 200

        budget_from_response = BudgetSchema.model_validate(response.json())
        assert budget_from_response.id == created_budget.id

    @pytest.mark.asyncio
    async def test_get_budget_by_id_unauthenticated(self, async_client):
        response = await async_client.get(f"{BUDGET_BASE_PATH}/1")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_budget_by_id_non_existent(self, authenticated_client):
        response = await authenticated_client.get(f"{BUDGET_BASE_PATH}/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_budget_route(
        self, create_budget_request, authenticated_client, budget_update_payload, user
    ):
        created = await create_budget_request()
        assert created.status_code == 201
        created_budget = BudgetSchema.model_validate(created.json())

        update_response = await authenticated_client.patch(
            f"{BUDGET_BASE_PATH}/{created_budget.id}",
            data=budget_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 200

        updated = BudgetSchema.model_validate(update_response.json())
        assert updated.id == created_budget.id
        assert updated.amount_limit == budget_update_payload.amount_limit
        assert updated.month_year == budget_update_payload.month_year
        assert str(updated.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_update_budget_invalid_data(
        self, create_budget_request, authenticated_client, budget_update_payload, user
    ):
        created = await create_budget_request()
        assert created.status_code == 201
        created_budget = BudgetSchema.model_validate(created.json())

        created_budget.category_id = 99999999

        update_response = await authenticated_client.patch(
            f"{BUDGET_BASE_PATH}/{created_budget.id}",
            data=created_budget.model_dump_json(),
        )

        assert update_response.status_code == 200

        updated = BudgetSchema.model_validate(update_response.json())
        assert updated.id == created_budget.id
        assert updated.amount_limit == budget_update_payload.amount_limit
        assert updated.month_year == budget_update_payload.month_year
        assert str(updated.user_id) == str(user.uid)

    @pytest.mark.asyncio
    async def test_user_cannot_update_other_user_budget(
        self, authenticated_client, budget_factory, second_user, budget_update_payload
    ):
        other_user_budget = await budget_factory(user_id=second_user.uid)

        update_response = await authenticated_client.patch(
            f"{BUDGET_BASE_PATH}/{other_user_budget.id}",
            data=budget_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_budget_unauthenticated(
        self, async_client, budget_factory, user, budget_update_payload
    ):
        budget = await budget_factory(user_id=user.uid)

        update_response = await async_client.patch(
            f"{BUDGET_BASE_PATH}/{budget.id}",
            data=budget_update_payload.model_dump_json(),
        )

        assert update_response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_budget_route(
        self, create_budget_request, authenticated_client
    ):
        created = await create_budget_request()
        assert created.status_code == 201
        budget_id = created.json()["id"]

        delete_response = await authenticated_client.delete(
            f"{BUDGET_BASE_PATH}/{budget_id}"
        )
        assert delete_response.status_code == 200

        get_response = await authenticated_client.get(f"{BUDGET_BASE_PATH}/{budget_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_non_existent_budget(self, authenticated_client):
        response = await authenticated_client.delete(f"{BUDGET_BASE_PATH}/999999")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_budget_unauthenticated(
        self, create_budget_request, authenticated_client
    ):
        created = await create_budget_request()
        assert created.status_code == 201
        budget_id = created.json()["id"]

        authenticated_client.headers.pop("Authorization", None)
        response = await authenticated_client.delete(f"{BUDGET_BASE_PATH}/{budget_id}")

        assert response.status_code == 401
