from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.expense.schemas import ExpenseCreateSchema
from src.domain.expense.service import ExpenseService
from src.errors.main import EntityNotFoundException


class TestExpenseService:
    @pytest.mark.asyncio
    async def test_create_expense_uses_authenticated_user_id(
        self, db_session, user, category
    ):
        service = ExpenseService(db_session)
        payload = ExpenseCreateSchema(
            category_id=category.id,
            amount=Decimal("12.50"),
            transaction_date=datetime.now(timezone.utc),
            note="coffee",
        )

        created = await service.create(payload, user.uid)

        assert created.user_id == user.uid
        assert created.category_id == category.id
        assert created.amount == Decimal("12.50")

    @pytest.mark.asyncio
    async def test_delete_requires_expense_ownership(self, db_session, user, category):
        service = ExpenseService(db_session)
        payload = ExpenseCreateSchema(
            category_id=category.id,
            amount=Decimal("20.00"),
            transaction_date=datetime.now(timezone.utc),
            note="transport",
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
    async def test_get_by_id_blocks_cross_user_access(self, db_session, user, category):
        service = ExpenseService(db_session)
        payload = ExpenseCreateSchema(
            category_id=category.id,
            amount=Decimal("9.99"),
            transaction_date=datetime.now(timezone.utc),
            note="cross-user check",
        )
        created = await service.create(payload, user.uid)

        with pytest.raises(EntityNotFoundException):
            await service.get_by_id(object_id=created.id, user_id=uuid4())
