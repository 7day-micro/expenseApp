import pytest
from decimal import Decimal

from src.domain.expense.schemas import ExpenseUpdateSchema, ExpenseSchema


class TestExpenseRoutes:
    @pytest.mark.asyncio
    async def test_create(self, authenticated_client, user, valid_expense_payload):
        payload = valid_expense_payload

        response = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )

        assert response.status_code == 201
        data = ExpenseSchema.model_validate(response.json())

        assert data.id is not None
        assert str(data.user_id) == str(user.uid)
        assert data.category_id == payload.category_id

    @pytest.mark.asyncio
    async def test_create_invalid_payload(
        self, authenticated_client, user, valid_expense_payload
    ):
        payload = valid_expense_payload

        payload.amount = None

        response = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_unauthenticated(
        self, async_client, valid_expense_payload, user
    ):
        payload = valid_expense_payload

        response = await async_client.post("/expenses/", data=payload.model_dump_json())

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_expenses_route(
        self,
        authenticated_client,
        valid_expense_payload,
    ):

        for i in range(3):
            await authenticated_client.post(
                "/expenses/", data=valid_expense_payload.model_dump_json()
            )

        response = await authenticated_client.get("/expenses/")

        assert response.status_code == 200
        data = list(map(ExpenseSchema.model_validate, response.json()))

        for expense in data:
            ExpenseSchema.model_validate(expense)

        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_list_unauthenticated(
        self,
        async_client,
        valid_expense_payload,
    ):
        response = await async_client.get("/expenses/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_only_own_expenses(
        self, user_factory, expense_factory, authenticated_client, user, second_user, category_factory
    ):
        category1 = await category_factory(user_id = user.uid)
        category2 = await category_factory(user_id = second_user.uid)
        
        for _ in range(30):
            await expense_factory(user_id=user.uid,category_id=category1.id)
            await expense_factory(user_id=second_user.uid, category_id=category2.id)

        response = await authenticated_client.get("/expenses/")

        assert response.status_code == 200
        data = list(map(ExpenseSchema.model_validate, response.json()))
        assert all(str(expense.user_id) == str(user.uid) for expense in data)
        assert len(data) == 30

    @pytest.mark.asyncio
    async def test_get_expense_by_id_route(
        self, authenticated_client, valid_expense_payload
    ):
        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201
        created_expense = ExpenseSchema.model_validate(created.json())

        response = await authenticated_client.get(f"/expenses/{created_expense.id}")

        assert response.status_code == 200

        expense_from_response = ExpenseSchema.model_validate(response.json())

        assert expense_from_response.id == created_expense.id

    @pytest.mark.asyncio
    async def test_get_expense_by_id_unauthenticated(
        self, async_client, user, category
    ):

        created = await async_client.get(f"/expenses/{category.id}")
        assert created.status_code == 401

    @pytest.mark.asyncio
    async def test_get_by_id_non_existent(self, authenticated_client):
        response = await authenticated_client.get(f"/expenses/{3}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_expense_route(
        self, authenticated_client, user, valid_expense_payload
    ):
        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201
        expense = ExpenseSchema.model_validate(created.json())

        update_payload = ExpenseUpdateSchema(
            amount=valid_expense_payload.amount + Decimal("10.00"), note="Updated note"
        )
        update_resp = await authenticated_client.patch(
            f"/expenses/{expense.id}", data=update_payload.model_dump_json()
        )

        assert update_resp.status_code == 200

        expense_response = ExpenseSchema.model_validate(update_resp.json())

        assert expense_response.amount == update_payload.amount
        assert expense_response.note == update_payload.note
        assert expense_response.id == expense.id
        assert expense_response.user_id == user.uid
        assert expense_response.category_id == payload.category_id

    @pytest.mark.asyncio
    async def test_user_update_other_user_expense(
        self,
        authenticated_client,
        user,
        valid_expense_payload,
        second_user,
        expense_factory,
        category
    ):

        expense1 = await expense_factory(user_id=second_user.uid, category_id = category.id)

        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201

        update_payload = ExpenseUpdateSchema(
            amount=valid_expense_payload.amount + Decimal("10.00"), note="Updated note"
        )
        update_resp = await authenticated_client.patch(
            f"/expenses/{expense1.id}", data=update_payload.model_dump_json()
        )

        assert update_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_expense_route_unauthenticated(
        self, async_client, valid_expense_payload, user, expense_factory, category
    ):

        expense = await expense_factory(user_id=user.uid, category_id = category.id)

        update_payload = ExpenseUpdateSchema(
            amount=valid_expense_payload.amount + Decimal("10.00"), note="Updated note"
        )
        update_resp = await async_client.patch(
            f"/expenses/{expense.id}", data=update_payload.model_dump_json()
        )

        assert update_resp.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_expense_route(
        self, authenticated_client, user, valid_expense_payload
    ):
        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201
        expense_id = created.json()["id"]

        del_resp = await authenticated_client.delete(f"/expenses/{expense_id}")
        assert del_resp.status_code == 200

        get_resp = await authenticated_client.get(f"/expenses/{expense_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_user_try_delete_non_existent_expense(
        self, authenticated_client, user, valid_expense_payload
    ):
        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201

        del_resp = await authenticated_client.delete(f"/expenses/{399999}")

        assert del_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_unauthenticated(
        self, authenticated_client, valid_expense_payload
    ):
        payload = valid_expense_payload
        created = await authenticated_client.post(
            "/expenses/", data=payload.model_dump_json()
        )
        assert created.status_code == 201
        expense_id = created.json()["id"]

        authenticated_client.headers.pop("Authorization", None)
        del_resp = await authenticated_client.delete(f"/expenses/{expense_id}")
        assert del_resp.status_code == 401


    @pytest.mark.asyncio
    async def test_404_error_returns_request_id(self, authenticated_client):
        """
        Test that requesting a non-existent entity triggers the global exception handler
        and correctly populates the request_id in the JSON body.
        """
        response = await authenticated_client.get("/expenses/999999")
        
        assert response.status_code == 404
        
        data = response.json()
        
        assert data["success"] is False
        assert "error" in data
        
        request_id = data["error"].get("request_id")
        assert request_id is not None, "request_id should not be null"
        assert isinstance(request_id, str), "request_id should be a string (UUID)"
