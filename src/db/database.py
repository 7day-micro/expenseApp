from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event
from datetime import datetime, timezone

from src.config import settings

SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}"


def engine_factory(*args, **kwargs):
    return create_async_engine(*args, **kwargs)


engine = engine_factory(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_size=30,
    max_overflow=5,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True,
)

@event.listens_for(engine.sync_engine, 'before_cursor_execute')
def track_start_time(conn, cursor, statemetn, parameters, context, executemany):
    context._start_time = datetime.now(tz=timezone.utc)

@event.listens_for(engine.sync_engine, 'after_cursor_execute')
def track_total_time(conn, cursor, statemetn, parameters, context, executemany):
    context._time_taken = datetime.now(tz=timezone.utc) - context._start_time


# Session
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with SessionLocal() as session:
        yield session
