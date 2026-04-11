from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.oauth2 import get_current_user
from src.db.database import get_db
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    MetricsOverview,
)
from src.domain.expense.service import ExpenseMetricGenerator, ExpenseService
from src.models import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/", response_model=ExpenseSchema, status_code=status.HTTP_201_CREATED)
async def create_expense(
    payload: ExpenseCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    return await service.create(payload, current_user.uid)


@router.get("/", response_model=list[ExpenseSchema])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date: date | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
):
    service = ExpenseService(db)
    return await service.get_all(
        user_id=current_user.uid,
        date_filter=date,
        start_date=start_date,
        end_date=end_date,
        min_value=min_value,
        max_value=max_value,
    )


@router.get("/metrics", response_model=MetricsOverview)
async def metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseMetricGenerator(db, current_user.uid)

    return await service.run()


@router.get("/{expense_id}", response_model=ExpenseSchema)
async def get_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    return await service.get_by_id(expense_id, current_user.uid)


@router.patch("/{expense_id}", response_model=ExpenseSchema)
async def update_expense(
    expense_id: int,
    payload: ExpenseUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    return await service.update(expense_id, payload, current_user.uid)


@router.delete("/{expense_id}", response_model=ExpenseSchema)
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    return await service.delete(expense_id, current_user.uid)
