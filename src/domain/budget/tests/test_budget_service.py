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
    """
    Create and return a second category with a deterministic unique name for tests.

    This function sets the provided category payload's name to "Second Category" and persists it for the given user.

    Parameters:
        valid_category: Category creation payload whose `name` will be set to "Second Category" before creation.

    Returns:
        The created category instance.
    """
    service = CategoryService(db_session)
    # Garante um nome único para evitar IntegrityError de duplicidade
    valid_category.name = "Second Category"
    return await service.create(data=valid_category, user_id=user.uid)


class TestBudgetService:
    @pytest.mark.asyncio
    async def test_create_budget(self, db_session, valid_budget_payload, user):
        service = BudgetService(db_session)
        budget = await service.create(
            data=valid_budget_payload, user_id= user.uid
        )

        assert budget.amount_limit == valid_budget_payload.amount_limit
        assert budget.category_id == valid_budget_payload.category_id

    @pytest.mark.asyncio
    async def test_get_by_id_raises_not_found(self, db_session, user):
        service = BudgetService(db_session)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=999999, user_id=user.uid)

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
        second_category,
        budget_factory,
    ):
        service = BudgetService(db_session)

        update_data = BudgetUpdateSchema(
            amount_limit=valid_budget_payload.amount_limit + 10,
            category_id=second_category.id,
            month_year=timedelta(days=30) + valid_budget_payload.month_year,
        )

        with pytest.raises(EntityNotFoundException):
            await service.update(
                object_id=budget.id,
                data=update_data,
                user_id=(await user_factory()).uid,
            )

    @pytest.mark.asyncio
    async def test_get_all_budgets(self, budget_factory, db_session, user, second_user):
        service = BudgetService(db_session)

        # Cria 3 budgets para o mesmo usuário
        for _ in range(5):
            await budget_factory(user_id=user.uid)
            # interfence to ensure budgets are created for the second user as well, but they should not be returned in the query for the first user
            await budget_factory(user_id=second_user.uid)

        budgets = await service.get_all(user_id=user.uid)

        assert len(budgets) == 5
        assert all(budget.user_id == user.uid for budget in budgets)

    @pytest.mark.asyncio
    async def test_update_with_none_fields_dont_persists(
        self, user, db_session, budget_factory, category_factory
    ):
        c1 = await category_factory(user_id=user.uid)
        b1 = await budget_factory(user_id=user.uid, category_id=c1.id)
        service = BudgetService(db_session)

        await service.update(
            object_id=b1.id, data=BudgetUpdateSchema(), user_id=user.uid
        )

        assert b1.category_id is not None
        assert b1.amount_limit is not None
        assert b1.month_year is not None

        await service.update(
            object_id=b1.id,
            data=BudgetUpdateSchema(
                amount_limit=None, category_id=None, month_year=None
            ),
            user_id=user.uid,
        )

        assert b1.category_id is not None
        assert b1.amount_limit is not None
        assert b1.month_year is not None
