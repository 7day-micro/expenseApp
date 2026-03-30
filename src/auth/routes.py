from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.database import get_db
from src.models import User
from src.auth import schemas, oauth2

#router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(user_credentials: schemas.UserCreate, db: AsyncSession = Depends(get_db)):

    result = await db.execute(select(User).filter(User.email == user_credentials.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = oauth2.get_password_hash(user_credentials.password)
    
    new_user = User(
        username=user_credentials.username,
        email=user_credentials.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    
    result = await db.execute(select(User).filter(User.email == user_credentials.username))
    user = result.scalars().first()
    
    if not user or not oauth2.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Invalid Credentials"
        )
        
    access_token = oauth2.create_access_token(data={"user_id": str(user.uid)})
    
    return {"access_token": access_token, "token_type": "bearer"}
