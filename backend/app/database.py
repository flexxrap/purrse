from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_local = any(h in settings.DATABASE_URL for h in ("railway.internal", "localhost", "127.0.0.1"))
_ssl = False if _local else True

engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"ssl": _ssl},
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
