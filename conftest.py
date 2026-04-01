import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from src.auth.schemas import UserCreateSchema
from src.domain.category.schemas import CategoryCreateSchema
from src.main import app
from httpx import AsyncClient, ASGITransport
from src.db.database import get_db
from src.models import User, Category
from pytest import fixture
from sqlalchemy_utils import database_exists, drop_database, create_database
from pathlib import Path
from alembic import command
from alembic.config import Config
from src.config import db_url
from logging import getLogger
import logging

logging.basicConfig(level=logging.INFO)
logger = getLogger(__name__)

SYNC_URL = db_url.replace("postgresql+asyncpg://", "postgresql://")
ASYNC_URL = db_url


# ── Event loop: session-scoped so all fixtures share one loop ──────────────────
@fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── DB creation + Alembic migrations (sync, runs once) ────────────────────────
@fixture(scope="session", autouse=True)
def setup_test_database():
    if database_exists(SYNC_URL):
        drop_database(SYNC_URL)
    create_database(SYNC_URL)

    alembic_ini = Path.cwd() / "alembic.ini"
    if not alembic_ini.exists():
        raise FileNotFoundError("alembic.ini not found")

    cfg = Config(str(alembic_ini))
    cfg.set_main_option("sqlalchemy.url", SYNC_URL)
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations applied.")

    yield

    # NullPool means no open connections remain, so drop always succeeds
    drop_database(SYNC_URL)


# ── Single session-scoped engine with NullPool ────────────────────────────────
# NullPool = connections are closed immediately after use, never pooled.
# This fixes BOTH the "different loop" error AND "database in use" on teardown.
@pytest_asyncio.fixture(scope="session")
async def test_engine(setup_test_database):
    engine = create_async_engine(
        ASYNC_URL,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


# ── Per-test transactional session (rolled back after each test) ───────────────
@pytest_asyncio.fixture
async def db_session(test_engine):
    async with test_engine.connect() as connection:
        await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
        )

        async with session_factory() as session:
            await session.begin_nested()  # SAVEPOINT
            yield session

        await connection.rollback()


# ── HTTP client wired to the transactional session ────────────────────────────
@pytest_asyncio.fixture
async def async_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        client.headers.update({"Content-Type": "application/json"})
        yield client

    app.dependency_overrides.clear()


# ── Reusable fixtures ──────────────────────────────────────────────────────────
@fixture
def valid_user():
    return UserCreateSchema(
        username="testuser",
        email="expenseapp@example.com",
        password="StrongePassWord123#",
    )


@pytest_asyncio.fixture
async def user(db_session, valid_user):
    from src.auth.oauth2 import get_password_hash

    u = User(
        username=valid_user.username,
        email=valid_user.email,
        password_hash=get_password_hash(valid_user.password),
    )
    db_session.add(u)
    await (
        db_session.flush()
    )  # write within transaction, don't commit    await db_session.refresh(user)

    return u


@pytest_asyncio.fixture
async def admin_user(db_session, user):
    user.role = "admin"
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@fixture
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
