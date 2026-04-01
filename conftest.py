from decimal import Decimal
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.schemas import UserCreateSchema
from src.db.database import SQLALCHEMY_DATABASE_URL, engine_factory
from src.domain.category.schemas import CategoryCreateSchema
from src.main import app

from httpx import AsyncClient, ASGITransport
from src.db.database import get_db
from src.models import User, Category
from src.domain.expense.schemas import ExpenseCreateSchema
from src.domain.budget.schemas import BudgetCreateSchema
from src.models import Budget

from src.auth.schemas import LoginSchema


from faker import Faker


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
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def user_factory(db_session):
    from src.auth.oauth2 import get_password_hash

    fake = Faker()
    created = []

    async def _factory(username=None, email=None, password="StrongPass123#"):
        user = User(
            username=username or fake.user_name(),
            email=email or fake.email(),
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        created.append(user)
        return user

    return _factory


@pytest_asyncio.fixture
async def admin_user(db_session, user):
    user.role = "admin"
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def valid_category(user) -> CategoryCreateSchema:
    return CategoryCreateSchema(
        name="Valid Category",
        user_id=user.uid,
        color_icon="test_color_icon",
    )


@pytest_asyncio.fixture
async def category(db_session, valid_category, user):
    category = Category(
        name=valid_category.name,
        color_icon=valid_category.color_icon,
        user_id=user.uid,
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest.fixture
def valid_expense_payload(category):
    return ExpenseCreateSchema(
        category_id=category.id,
        amount=Decimal("12.50"),
        transaction_date=datetime.now(timezone.utc),
        note="coffee",
    )


@pytest.fixture
def valid_budget_payload(category, user):
    return BudgetCreateSchema(
        user_id=user.uid,
        category_id=category.id,
        amount_limit=Decimal("12.50"),
        month_year=datetime.now(timezone.utc),
        note="coffee",
    )


@pytest_asyncio.fixture
async def budget(db_session, category, valid_budget_payload):
    budget = Budget(**valid_budget_payload.model_dump())

    db_session.add(budget)
    await db_session.commit()
    await db_session.refresh(budget)

    return budget


@pytest_asyncio.fixture
async def authenticated_client(async_client, user, valid_user):
    payload = LoginSchema(email=user.email, password=valid_user.password)
    response = await async_client.post(
        "/auth/login",
        data=payload.model_dump_json(),
    )

    async_client.headers.update(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )

    return async_client
