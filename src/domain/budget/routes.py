from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.oauth2 import get_current_user
from src.db.database import get_db
from src.domain.budget.schemas import BudgetUpdateSchema, BudgetCreateSchema, BudgetSchema
from src.domain.budget.service import BudgetService
from src.models import User

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.post("/", response_model=BudgetSchema, status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BudgetService(db)
    return await service.create(payload, current_user.uid)


@router.get("/", response_model=list[BudgetSchema])
async def list_budget(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BudgetService(db)
    return await service.get_all(current_user.uid)


@router.get("/{budget_id}", response_model=BudgetSchema)
async def get_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BudgetService(db)
    return await service.get_by_id(budget_id, current_user.uid)


@router.patch("/{budget_id}", response_model=BudgetSchema)
async def update_budget(
    budget_id: int,
    payload: BudgetUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BudgetService(db)
    return await service.update(budget_id, payload, current_user.uid)


@router.delete("/{budget_id}", response_model=BudgetSchema)
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BudgetService(db)
    return await service.delete(budget_id, current_user.uid)
