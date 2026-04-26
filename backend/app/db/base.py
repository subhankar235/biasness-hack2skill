from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from typing import AsyncGenerator

from app.config import settings

class Base(DeclarativeBase):
    pass

_engine = None
_async_session = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine

def get_async_session():
    global _async_session
    if _async_session is None:
        _async_session = sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async_session = get_async_session()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()