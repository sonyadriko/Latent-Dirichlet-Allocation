"""
Database Session Management

Provides async SQLAlchemy engine and session management for SQLite.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

import logging

logger = logging.getLogger(__name__)

# SQLAlchemy Base for declarative models
Base = declarative_base()

# Global engine and session maker
_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def get_engine() -> AsyncEngine:
    """Get the current database engine."""
    global _engine
    if _engine is None:
        from config import Config
        _engine = create_async_engine(
            Config.DATABASE_URL,
            echo=False,  # Set to True for SQL query logging
            poolclass=StaticPool,  # SQLite doesn't need connection pooling
            connect_args={"check_same_thread": False}  # Needed for SQLite
        )
        logger.info(f"Database engine created: {Config.DATABASE_URL}")
    return _engine


def get_session_maker() -> async_sessionmaker:
    """Get the session maker factory."""
    global _async_session_maker
    if _async_session_maker is None:
        engine = get_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        logger.info("Session maker created")
    return _async_session_maker


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get a database session.

    Usage in FastAPI endpoints:
        @router.get("/items")
        async def get_items(session: AsyncSession = Depends(get_session)):
            ...

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.

    Usage:
        async with get_session_context() as session:
            await session.execute(...)

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database():
    """
    Initialize the database by creating all tables.

    This should be called on application startup.
    """
    from config import Config

    # Ensure data directory exists
    import os
    os.makedirs(os.path.dirname(Config.DATABASE_URL.replace("sqlite+aiosqlite:///", "")), exist_ok=True)

    engine = get_engine()
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered with Base
        from models.db_models import User, Project, PipelineRun, Document

        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables created")


async def close_database():
    """
    Close the database connection.

    This should be called on application shutdown.
    """
    global _engine, _async_session_maker

    if _engine:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        logger.info("Database connection closed")


async def reset_database():
    """
    Drop and recreate all tables.

    WARNING: This will delete all data! Use only for testing.
    """
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    logger.warning("Database reset - all tables dropped and recreated")
