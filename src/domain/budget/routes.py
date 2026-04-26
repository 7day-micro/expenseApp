from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.oauth2 import get_current_user
from src.db.database import get_db
from src.domain.budget.schemas import (
    BudgetCreateSchema,
    BudgetSchema,
    BudgetUpdateSchema,
)
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
    """
    Update an existing budget owned by the authenticated user.
    
    Parameters:
        budget_id (int): ID of the budget to update.
        payload (BudgetUpdateSchema): Fields to update on the budget.
    
    Returns:
        BudgetSchema: The updated budget.
    """
    service = BudgetService(db)
    return await service.update(budget_id, payload, current_user.uid)


@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a budget belonging to the authenticated user.
    
    Parameters:
        budget_id (int): ID of the budget to delete.
    
    Returns:
        Response: HTTP 204 No Content response.
    """
    service = BudgetService(db)
    await service.delete(budget_id, current_user.uid)
    return Response(status_code=204)
