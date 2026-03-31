from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models import User
from src.auth import oauth2
from src.auth.schemas import UserCreateSchema, LoginSchema


async def create_user_service(user_credentials: UserCreateSchema, db: AsyncSession):
    # check email existing
    result = await db.execute(select(User).filter(User.email == user_credentials.email))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Cript
    hashed_password = oauth2.get_password_hash(user_credentials.password)
    new_user = User(
        username=user_credentials.username,
        email=user_credentials.email,
        password_hash=hashed_password,
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def login_user_service(user_credentials: LoginSchema, db: AsyncSession):
    # user
    result = await db.execute(select(User).filter(User.email == user_credentials.email))
    user = result.scalars().first()

    # credentials
    if not user or not oauth2.verify_password(
        user_credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid credentials"
        )

    # token
    access_token = oauth2.create_access_token(data={"user_id": str(user.uid)})
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token_schema, db: AsyncSession):
    return oauth2.get_current_user(token_schema, db)
