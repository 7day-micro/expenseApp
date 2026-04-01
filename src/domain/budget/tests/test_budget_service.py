import pytest

from src.domain.budget.service import BudgetService
from src.exceptions import EntityNotFoundException


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
