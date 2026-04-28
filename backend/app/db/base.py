# app/db/base.py

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from typing import AsyncGenerator


class Base(DeclarativeBase):
    pass


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            "sqlite+aiosqlite:///./fairlens.db",
            echo=False,
        )
    return _engine


AsyncSessionLocal = sessionmaker(
    bind=get_engine(),
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session