from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.expense.service import ExpenseService
from src.exceptions import EntityNotFoundException


class TestExpenseService:
    @pytest.mark.asyncio
    async def test_create_expense_uses_authenticated_user_id(
        self, db_session, user, category, valid_expense_payload
    ):
        service = ExpenseService(db_session)
        payload = valid_expense_payload

        created = await service.create(payload, user.uid)

        assert created.user_id == user.uid
        assert created.category_id == category.id
        assert created.amount == Decimal("12.50")

    @pytest.mark.asyncio
    async def test_delete_requires_expense_ownership(
        self, db_session, user, valid_expense_payload
    ):
        service = ExpenseService(db_session)
        payload = valid_expense_payload.model_copy(
            update={"amount": Decimal("20.00"), "note": "transport"}
        )
        created = await service.create(payload, user.uid)

        with pytest.raises(EntityNotFoundException):
            await service.delete(created.id, uuid4())

        still_exists = await service.get_by_id(created.id, user.uid)
        assert still_exists is not None

    @pytest.mark.asyncio
    async def test_get_all_returns_empty_list_when_user_has_no_expenses(
        self, db_session
    ):
        service = ExpenseService(db_session)
        result = await service.get_all(uuid4())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_by_id_raises_for_nonexistent_expense_id(self, db_session):
        service = ExpenseService(db_session)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=999999, user_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_by_id_blocks_cross_user_access(
        self, db_session, user, valid_expense_payload
    ):
        service = ExpenseService(db_session)
        payload = valid_expense_payload.model_copy(
            update={"amount": Decimal("9.99"), "note": "cross-user check"}
        )
        created = await service.create(payload, user.uid)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=created.id, user_id=uuid4())

    @pytest.mark.asyncio
    async def test_get_all_expenses(
        self, db_session, user, expense_factory, category_factory
    ):
        service = ExpenseService(db_session)

        # Create multiple expenses for the user
        category = await category_factory(user_id=user.uid)

        for i in range(5):
            await expense_factory(
                user_id=user.uid,
                category_id=category.id,
                amount=Decimal("10.00"),
                note=f"Expense {i + 1}",
            )

        expenses = await service.get_all(user.uid)

        assert len(expenses) == 5
