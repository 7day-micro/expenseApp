from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.auth import schemas, service
from src.auth.oauth2 import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserResponseSchema,
)
async def create_user(
    user_credentials: schemas.UserCreateSchema, db: AsyncSession = Depends(get_db)
):
    # service
    return await service.create_user_service(user_credentials, db)


@router.post("/login", response_model=schemas.TokenSchema)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    # service
    return await service.login_user_service(user_credentials, db)


@router.get("/me", response_model=schemas.UserResponseSchema)
async def get_me(user: schemas.UserResponseSchema = Depends(get_current_user)):
    # Se o código chegar aqui, o 'user' já foi validado e buscado no banco
    return user
