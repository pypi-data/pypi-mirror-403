import os
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi import Depends
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis
from .db.subscriptions.models import Subscription, Profile, ApiKey
from sqlalchemy.future import select

engine = None
AsyncSessionLocal = None
RedisUrl = None

RedisKeyPrefix = "user:sub:auth"


def init_session(sqlite_path, redis_url):

    global AsyncSessionLocal, engine, RedisUrl

    db_dir = sqlite_path.parent
    if not db_dir.exists():
        raise ValueError(f"Directory does not exist: {db_dir}")

    # --- CONFIGURATION ---
    # SQLite URL for AsyncIO
    db_url = f"sqlite+aiosqlite:///{sqlite_path}"

    RedisUrl = os.getenv("REDIS_URL", "redis://localhost:6379/4")

    # --- DATABASE SETUP ---
    # connect_args={"check_same_thread": False} is required for SQLite in multithreaded apps (FastAPI)
    engine = create_async_engine(
        db_url, echo=False, connect_args={"check_same_thread": False}
    )

    # The session factory
    AsyncSessionLocal = sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )



async def init_subscription_models():
    global engine

    print(f"Checking Subscriptions DB...")

    from sqlalchemy import text
    from sqlalchemy.orm import relationship, declarative_base

    Base = declarative_base()

    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

    # Enable Write-Ahead Logging (WAL) for concurrency
    # This must be done on a direct connection, not a transaction block
    async with engine.connect() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        print("SQLite WAL Mode Enabled.")

    await engine.dispose()


async def get_db():
    """
    Dependency to provide an Async Database Session per request.
    Closes the session automatically when the request finishes.
    """

    global AsyncSessionLocal, engine

    if not AsyncSessionLocal:
        raise RuntimeError("subscriptions db connection not set up. You must call 'init_subs' before any routes that use 'validate_access'")

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_redis():
    """
    Dependency to provide a Redis client.
    """
    global RedisUrl
    client = Redis.from_url(RedisUrl, decode_responses=True)
    try:
        yield client
    finally:
        await client.close()


