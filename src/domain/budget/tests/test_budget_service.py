import pytest

from src.domain.budget.service import BudgetService
from src.exceptions import EntityNotFoundException

from src.domain.category.service import CategoryService


class TestBudgetService:
    @pytest.mark.asyncio
    async def test_create_budget(self, db_session, valid_budget_payload):
        service = BudgetService(db_session)
        budget = await service.create(
            data=valid_budget_payload, user_id=valid_budget_payload.user_id
        )

        assert budget.amount_limit == valid_budget_payload.amount_limit
        assert budget.category_id == valid_budget_payload.category_id

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, db_session, budget):
        service = BudgetService(db_session)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=999999, user_id=budget.user_id)

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session, budget, user):
        service = BudgetService(db_session)
        result = await service.get_by_id(object_id=budget.id, user_id=user.uid)

        assert result is not None
        assert result.id == budget.id
        assert result.amount_limit == budget.amount_limit
        assert result.category_id == budget.category_id
        assert result.user_id == budget.user_id

    @pytest.mark.asyncio
    async def test_delete_budget(self, db_session, budget, user):
        service = BudgetService(db_session)

        result = await service.get_by_id(object_id=budget.id, user_id=user.uid)
        await service.delete(object_id=budget.id, user_id=user.uid)

        assert result is not None
        assert result.id == budget.id

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=budget.id, user_id=user.uid)

    @pytest.mark.asyncio
    async def test_update_budget_amount_limit(
        self, db_session, budget, user, valid_budget_payload
    ):
        service = BudgetService(db_session)

        updated_payload = valid_budget_payload.copy()
        updated_payload.amount_limit = updated_payload.amount_limit + 10

        await service.update(object_id=budget.id, user_id=user.uid, data={})

        result = await service.get_by_id(object_id=budget.id, user_id=user.uid)
        assert result.amount_limit == updated_payload.amount_limit

    @pytest.mark.asyncio
    async def test_update_budget_category_id(
        self, db_session, budget, user, valid_budget_payload, valid_category
    ):
        service = BudgetService(db_session)

        ### New category setup
        category_service = CategoryService(db_session)
        valid_category.name = valid_category.name + "new_name"
        result = await category_service.create(data=valid_category, user_id=user.uid)

        updated_payload = valid_budget_payload.copy()
        updated_payload.category_id = result.id

        await service.update(
            object_id=budget.id, user_id=user.uid, data=updated_payload
        )

        result = await service.get_by_id(object_id=budget.id, user_id=user.uid)
        assert result.amount_limit == updated_payload.amount_limit

    @pytest.mark.asyncio
    async def test_budget_update_dont_change_user_id(self, db_session, budget, user):
        service = BudgetService(db_session)

        new_amount_limit = budget.amount_limit + 10
        new_category_id = budget.category_id + 1 if budget.category_id else 1

        updated_budget = await service.update(
            object_id=budget.id,
            user_id=user.uid,
            data={
                "amount_limit": new_amount_limit,
                "category_id": new_category_id,
            },
        )

        assert updated_budget is not None
        assert updated_budget.id == budget.id
        assert updated_budget.amount_limit == new_amount_limit
        assert updated_budget.category_id == new_category_id
        assert updated_budget.user_id == budget.user_id
