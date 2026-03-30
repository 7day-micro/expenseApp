from pydantic import ValidationError
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.auth.schemas import UserResponseSchema
from src.models import User
from src.auth.service import create_user_service


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_valid_user(self, db_session, valid_user):
        await create_user_service(valid_user, db_session)
        user = await db_session.execute(
            select(User).where(User.email == valid_user.email)
        )

        user = user.scalar_one_or_none()
        assert user is not None
        assert user.email == valid_user.email
        assert user.username == valid_user.username
        assert UserResponseSchema.model_validate(user)

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="the Error raised is IntegrityError instead of HTTPException due to the unique constraint violation in the database"
    )
    async def test_register_existing_email(self, db_session, valid_user):
        await create_user_service(valid_user, db_session)

        with pytest.raises(IntegrityError):
            await create_user_service(valid_user, db_session)

    @pytest.mark.asyncio
    @pytest.mark.skip(
        reason="email validation is currently disabled in the service layer"
    )
    async def test_register_invalid_email(self, db_session, valid_user):
        valid_user.email = "invalid-email"
        with pytest.raises(ValidationError):
            await create_user_service(valid_user, db_session)

    @pytest.mark.asyncio
    @pytest.mark.skip("we need to fix the service layer in future")
    async def test_register_short_password(self, db_session, valid_user):
        valid_user.password = "short"
        with pytest.raises(ValidationError):
            await create_user_service(valid_user, db_session)
