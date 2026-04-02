from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.oauth2 import get_current_user
from src.db.database import get_db
from src.domain.category.schemas import (
    CategoryCreateSchema,
    CategorySchema,
    CategoryUpdateSchema,
)
from src.domain.category.service import CategoryService

from src.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return await service.create(payload, current_user.uid)


@router.get("/", response_model=list[CategorySchema])
async def list_category(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return await service.get_all(current_user.uid)


@router.get("/{category_id}", response_model=CategorySchema)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return await service.get_by_id(category_id, current_user.uid)


@router.patch("/{category_id}", response_model=CategorySchema)
async def update_category(
    category_id: int,
    payload: CategoryUpdateSchema,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return await service.update(category_id, payload, current_user.uid)


@router.delete("/{category_id}", response_model=CategorySchema)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = CategoryService(db)
    return await service.delete(category_id, current_user.uid)
