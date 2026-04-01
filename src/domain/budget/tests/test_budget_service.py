import pytest
import pytest_asyncio
import copy

from src.domain.budget.service import BudgetService
from src.exceptions import EntityNotFoundException

from src.domain.category.service import CategoryService
from src.domain.budget.schemas import BudgetUpdateSchema
from datetime import timedelta


@pytest_asyncio.fixture
async def second_category(db_session, user, valid_category):
    service = CategoryService(db_session)
    # Garante um nome único para evitar IntegrityError de duplicidade
    valid_category.name = "Second Category"
    return await service.create(data=valid_category, user_id=user.uid)


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
    async def test_update_budget(
        self, db_session, budget, user, valid_budget_payload, second_category
    ):
        service = BudgetService(db_session)

        update_data = BudgetUpdateSchema(
            amount_limit=valid_budget_payload.amount_limit + 10,
            category_id=second_category.id,
            month_year=timedelta(days=30) + valid_budget_payload.month_year,
        )

        t0 = copy.deepcopy(
            await service.get_by_id(object_id=budget.id, user_id=user.uid)
        )

        await service.update(object_id=budget.id, data=update_data, user_id=user.uid)

        t1 = await service.get_by_id(object_id=budget.id, user_id=user.uid)

        assert t0.amount_limit != t1.amount_limit
        assert t1.amount_limit == update_data.amount_limit
        assert t1.category_id == update_data.category_id
        assert t1.month_year == update_data.month_year

    @pytest.mark.asyncio
    async def test_update_dont_change_user_id(
        self,
        db_session,
        budget,
        user_factory,
        valid_budget_payload,
        user,
        second_category,
    ):
        service = BudgetService(db_session)

        update_data = BudgetUpdateSchema(
            amount_limit=valid_budget_payload.amount_limit + 10,
            category_id=second_category.id,
            month_year=timedelta(days=30) + valid_budget_payload.month_year,
        )

        with pytest.raises(EntityNotFoundException):
            await service.update(
                object_id=budget.id, data=update_data, user_id=user_factory.uid
            )
