import pytest

from src.domain.budget.service import BudgetService


class TestBudgetService:
    @pytest.mark.asyncio
    async def test_create_budget(self, db_session, valid_budget_payload):
        service = BudgetService(db_session)
        budget = await service.create(
            data=valid_budget_payload, user_id=valid_budget_payload.user_id
        )

        assert budget.amount_limit == valid_budget_payload.amount_limit
        assert budget.category_id == valid_budget_payload.category_id
