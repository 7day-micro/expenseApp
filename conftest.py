import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreateSchema
from src.db.database import SQLALCHEMY_DATABASE_URL, engine_factory
from src.main import app

from httpx import AsyncClient, ASGITransport
from src.db.database import get_db
from src.models import User


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


@pytest_asyncio.fixture
async def async_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.headers.update({"Content-Type": "application/json"})
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def valid_user():
    return UserCreateSchema(
        username="testuser",
        email="expenseapp@example.com",
        password="StrongePassWord123#",
    )


@pytest_asyncio.fixture
async def user(db_session, valid_user):
    from src.auth.oauth2 import get_password_hash

    user = User(
        username=valid_user.username,
        email=valid_user.email,
        password_hash=get_password_hash(valid_user.password),
    )

    db_session.add(user)
    await db_session.commit() #await!

    return user


@pytest_asyncio.fixture
async def admin_user(db_session):
    from src.auth.oauth2 import get_password_hash

    admin = User(
        username="adminboss",
        email="admin@example.com",
        password_hash=get_password_hash("SuperAdmin123!"),
        role="admin"  #admin
    )

    db_session.add(admin)
    await db_session.commit()

    return admin