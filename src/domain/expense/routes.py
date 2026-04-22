import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.oauth2 import get_current_user
from src.db.database import get_db
from src.domain.expense.schemas import (
    ExpenseCreateSchema,
    ExpenseSchema,
    ExpenseUpdateSchema,
    PaginatedResponseSchema,
)
from src.domain.expense.service import ExpenseService
from src.domain.metrics.schemas import MetricsOverview
from src.domain.metrics.services.period_metrics_service import PeriodMetricsService
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


@router.get("/", response_model=PaginatedResponseSchema)
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    date: datetime.date | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    min_value: Decimal | None = None,
    max_value: Decimal | None = None,
    limit: int = Query(
        20, ge=1
    ),  # default is 20 and query param should be > =1 or error raised
    page: int = 1,
):
    service = ExpenseService(db)
    return await service.get_all(
        user_id=current_user.uid,
        date_filter=date,
        start_date=start_date,
        end_date=end_date,
        min_value=min_value,
        max_value=max_value,
        limit=limit,
        page=page,
    )


@router.get("/metrics", response_model=MetricsOverview)
async def metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    year: bool = True,
):

    service = PeriodMetricsService(
        session=db, user_id=current_user.uid, start_date=start_date, end_date=end_date
    )

    return await service.execute(with_range=start_date and end_date, last_year=year)


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


@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ExpenseService(db)
    await service.delete(expense_id, current_user.uid)

    return Response(status_code=204)
