from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.db.base import Base

# Determine connect args
is_sqlite = "sqlite" in settings.DATABASE_URL
async_connect_args = {"check_same_thread": False} if is_sqlite else {}
sync_connect_args = {"check_same_thread": False} if "sqlite" in settings.SYNC_DATABASE_URL else {}

# Asynchronous engine & session factory
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=async_connect_args
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Synchronous engine & session factory (used by seed.py and quick management)
sync_engine = create_engine(
    settings.SYNC_DATABASE_URL,
    echo=False,
    future=True,
    connect_args=sync_connect_args
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initializes all database tables asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def init_db_sync():
    """Initializes all database tables synchronously."""
    Base.metadata.create_all(bind=sync_engine)
