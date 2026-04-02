from fastapi import APIRouter, Depends, status
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
    user_credentials: schemas.LoginSchema,
    db: AsyncSession = Depends(get_db),
):
    #update
    tokens = await service.login_user_service(user_credentials, db)
    return tokens


@router.get("/me", response_model=schemas.UserResponseSchema)
async def get_me(user: schemas.UserResponseSchema = Depends(get_current_user)):
    # Se o código chegar aqui, o 'user' já foi validado e buscado no banco
    return user


# new refresh token router
@router.post("/refresh", response_model=schemas.TokenSchema)
async def refresh_token(
    token_data: schemas.RefreshRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint used by the frontend to obtain a new access token 
    when the previous one expires, using a valid refresh token.
    """
    tokens = await service.refresh_token_service(token_data.refresh_token, db)
    return tokens