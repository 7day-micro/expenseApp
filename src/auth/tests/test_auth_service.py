from pydantic import ValidationError
import pytest
from sqlalchemy import select

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

    @pytest.mark.asyncio
    async def test_register_existing_email(self, db_session, valid_user):
        await create_user_service(valid_user, db_session)

        with pytest.raises(Exception):
            await create_user_service(valid_user, db_session)

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, db_session, valid_user):
        valid_user.email = "invalid-email"
        with pytest.raises(ValidationError):
            await create_user_service(valid_user, db_session)
