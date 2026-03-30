import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreateSchema
from src.db.database import SQLALCHEMY_DATABASE_URL, engine_factory


@pytest_asyncio.fixture
async def db_session():
    async with engine_factory(SQLALCHEMY_DATABASE_URL).connect() as connection:
        # Start outer transaction
        trans = await connection.begin()

        # Bind session to the connection
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            # Trap internal 'await db.commit()'
            await session.begin_nested()

            yield session

            await session.close()

        # Roll back to leave the DB clean for the next function-scoped engine
        await trans.rollback()


@pytest.fixture
def valid_user():
    return UserCreateSchema(
        username="testuser",
        email="expenseapp@example.com",
        password="StrongePassWord123#",
    )
