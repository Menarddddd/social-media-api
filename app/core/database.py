from fastapi import Request
from upstash_redis import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.settings import settings


DATABASE_URL = settings.DATABASE_URL.get_secret_value()

engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
            await db.commit()

        except Exception:
            await db.rollback()
            raise


class Base(DeclarativeBase):
    pass


def get_upstash_redis():
    """Get Upstash Redis client using REST API."""
    return Redis(
        url=settings.UPSTASH_REDIS_REST_URL.get_secret_value(),
        token=settings.UPSTASH_REDIS_REST_TOKEN.get_secret_value(),
    )


def get_redis(request: Request):
    return request.app.state.redis
