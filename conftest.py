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
from src.models import Budget, Expense

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
    """
    Create and persist a User using values from the provided valid_user schema.

    The user's password is hashed and stored as the model's password_hash; the created User is committed to the database and refreshed before being returned.

    Parameters:
        valid_user: A schema containing `username`, `email`, and `password` to populate the new User.

    Returns:
        The persisted and refreshed `User` instance.
    """
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
async def second_user(db_session, valid_user):
    """
    Create and persist a User using values from the provided valid_user schema.

    The user's password is hashed and stored as the model's password_hash; the created User is committed to the database and refreshed before being returned.

    Parameters:
        valid_user: A schema containing `username`, `email`, and `password` to populate the new User.

    Returns:
        The persisted and refreshed `User` instance.
    """
    from src.auth.oauth2 import get_password_hash

    fake = Faker()

    user = User(
        username=fake.user_name(),
        email=fake.email(),
        password_hash=get_password_hash(valid_user.password),
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def user_factory(db_session):
    """
    Return an async factory that creates and persists User records for tests.

    The returned coroutine accepts optional `username`, `email`, and `password`, hashes the password, adds the User to the provided session, commits and refreshes it, then returns the persisted User model.

    Returns:
        async_factory (Callable[[Optional[str], Optional[str], str], Awaitable[User]]): An async function with signature
            _factory(username=None, email=None, password="StrongPass123#")
        that creates, persists, and returns a `User`.
    """
    from src.auth.oauth2 import get_password_hash

    fake = Faker()

    async def _factory(username=None, email=None, password="StrongPass123#"):
        """
        Create and persist a User with optional username, email, and password, and return the created instance.

        Parameters:
            username (str | None): Username to set on the new user. If None, a username is generated.
            email (str | None): Email to set on the new user. If None, an email is generated.
            password (str): Plaintext password to hash and store on the user (defaults to "StrongPass123#").

        Returns:
            User: The newly created and refreshed User model instance (persisted to the database).
        """
        user = User(
            username=username or fake.user_name(),
            email=email or fake.email(),
            password_hash=get_password_hash(password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _factory


@pytest_asyncio.fixture
async def admin_user(db_session, user_factory):
    """
    Promotes the given user to the "admin" role and persists the change to the database.

    Parameters:
        user (User): The user model to update.

    Returns:
        User: The updated user instance with role set to "admin".
    """
    admin_user = await user_factory(username="adminuser")

    admin_user.role = "admin"

    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def valid_category(user) -> CategoryCreateSchema:
    """
    Create a valid CategoryCreateSchema for tests linked to the given user.

    Parameters:
        user: User model whose `uid` will be assigned to the category's `user_id`.

    Returns:
        CategoryCreateSchema: Schema with name "Valid Category", color_icon "test_color_icon", and `user_id` taken from `user.uid`.
    """
    return CategoryCreateSchema(
        name="Valid Category",
        user_id=user.uid,
        color_icon="test_color_icon",
    )


@pytest_asyncio.fixture
async def category(db_session, valid_category, user):
    """
    Create and persist a Category using the provided category data and owner.

    Parameters:
        db_session: Async SQLAlchemy session bound to a transactional test connection.
        valid_category: Category creation schema containing `name` and `color_icon`.
        user: Persisted User model whose `uid` will be set as the category owner.

    Returns:
        Category: The newly created and refreshed Category model instance.
    """
    category = Category(
        name=valid_category.name,
        color_icon=valid_category.color_icon,
        user_id=user.uid,
    )

    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    return category


@pytest_asyncio.fixture
async def category_factory(db_session):
    """
    parameters:
    user_id : mandatory
    name : optional, default to a fake word
    color_icon : optional, default to a fake color name
    """
    fake = Faker()

    async def _factory(name=None, color_icon=None, user_id=None):
        category = Category(
            name=name or fake.word(),
            color_icon=color_icon or fake.color_name(),
            user_id=user_id,
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category

    return _factory


@pytest.fixture
def valid_expense_payload(category):
    """
    Create a valid ExpenseCreateSchema payload for the given category.

    Parameters:
        category: The category model whose `id` will be used as `category_id` in the payload.

    Returns:
        An `ExpenseCreateSchema` populated with `category_id`, an `amount` of 12.50, the current UTC `transaction_date`, and `note` set to "coffee".
    """
    return ExpenseCreateSchema(
        category_id=category.id,
        amount=Decimal("12.50"),
        transaction_date=datetime.now(timezone.utc),
        note="coffee",
    )


@pytest_asyncio.fixture
async def expense_factory(db_session):
    """
    parameters:
        category_id : mandatory
        amount : optional, default to Decimal("100.00")
        transaction_date : optional, default to current UTC datetime
        note : optional, default to a fake sentence
    """
    fake = Faker()

    async def _factory(
        user_id=None, category_id=None, amount=None, transaction_date=None, note=None
    ):
        expense = Expense(
            user_id=user_id,
            category_id=category_id,
            amount=amount
            or Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
            transaction_date=transaction_date or datetime.now(timezone.utc),
            note=note or fake.sentence(),
        )
        db_session.add(expense)
        await db_session.commit()
        await db_session.refresh(expense)
        return expense

    return _factory


@pytest.fixture
def valid_budget_payload(category, user):
    """
    Builds a BudgetCreateSchema payload for creating a budget tied to the given category and user.

    Parameters:
        category: The Category model instance whose `id` will be used as `category_id`.
        user: The User model instance whose `uid` will be used as `user_id`.

    Returns:
        A `BudgetCreateSchema` populated with `user_id`, `category_id`, `amount_limit` set to 12.50, `month_year` set to the current UTC datetime, and `note` set to "coffee".
    """
    return BudgetCreateSchema(
        user_id=user.uid,
        category_id=category.id,
        amount_limit=Decimal("12.50"),
        month_year=datetime.now(timezone.utc),
    )


@pytest_asyncio.fixture
async def budget(db_session, valid_budget_payload):
    """
    Create and persist a Budget model from the provided budget payload.

    Parameters:
        db_session: Async SQLAlchemy session used to persist the budget.
        category: Existing Category instance (ensures the referenced category exists).
        valid_budget_payload: BudgetCreateSchema containing the fields used to construct the Budget.

    Returns:
        The persisted Budget instance with database-populated fields (e.g., id, timestamps).
    """
    budget = Budget(**valid_budget_payload.model_dump())

    db_session.add(budget)
    await db_session.commit()
    await db_session.refresh(budget)

    return budget


@pytest_asyncio.fixture
async def budget_factory(db_session):
    """
    parameters:
        user_id : mandatory
        category_id : optional
        amount_limit : optional, default to Decimal("100.00")
        month_year : optional, default to current UTC datetime
        note : optional, default to a fake sentence
    """
    fake = Faker()

    async def _factory(
        user_id=None, category_id=None, amount_limit=None, month_year=None, note=None
    ):
        budget = Budget(
            user_id=user_id,
            category_id=category_id,
            amount_limit=amount_limit
            or Decimal(fake.pydecimal(left_digits=3, right_digits=2, positive=True)),
            month_year=month_year or datetime.now(timezone.utc),
        )
        db_session.add(budget)
        await db_session.commit()
        await db_session.refresh(budget)
        return budget

    return _factory


@pytest_asyncio.fixture
async def authenticated_client(async_client, user, valid_user):
    """
    Return an HTTP client whose Authorization header is set to a Bearer token for the provided user.

    This fixture logs in using the given user's credentials and updates the client's default headers with the retrieved access token.

    Returns:
        The `async_client` instance with its `Authorization` header set to `Bearer <access_token>`.
    """
    payload = LoginSchema(email=user.email, password=valid_user.password)
    response = await async_client.post(
        "/auth/login",
        data=payload.model_dump_json(),
    )

    assert response.status_code == 200, "Login failed in authenticated_client fixture"
    async_client.headers.update(
        {"Authorization": f"Bearer {response.json()['access_token']}"}
    )

    return async_client


@pytest_asyncio.fixture
async def authenticated_client_factory(db_session):
    clients = []

    async def _factory(user, password="StrongePassWord123#"):
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        client.headers.update({"Content-Type": "application/json"})
        app.dependency_overrides[get_db] = lambda: db_session

        payload = LoginSchema(email=user.email, password=password)
        response = await client.post("/auth/login", data=payload.model_dump_json())

        assert response.status_code == 200, f"Login failed for {user.email}"
        client.headers.update(
            {"Authorization": f"Bearer {response.json()['access_token']}"}
        )

        clients.append(client)
        return client

    yield _factory

    for client in clients:
        await client.aclose()
