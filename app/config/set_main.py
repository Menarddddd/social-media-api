import logging
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import (
    Base,
    AsyncSessionLocal,
)
from app.core.security import hash_password
from app.core.settings import settings
from app import models

from app.core.dependency import require_admin
from app.exceptions.exception import (
    BadRequestException,
    CredentialsException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.exceptions.handler import (
    bad_request_exception_handler,
    credentials_exception_handler,
    duplicate_entry_exception_handler,
    field_not_found_exception_handler,
)
from app.models.user import Role, User
from app.routers.user import router as user_router
from app.routers.post import router as post_router
from app.routers.comment import router as comment_router
from app.routers.admin import router as admin_router
from app.routers.health import router as health_router


logger = logging.getLogger(__name__)


def register_routers(app: FastAPI):
    app.include_router(health_router, prefix="/health", include_in_schema=False)
    app.include_router(user_router, prefix="/api/users", tags=["users"])
    app.include_router(post_router, prefix="/api/posts", tags=["posts"])
    app.include_router(comment_router, prefix="/api/comments", tags=["comments"])
    app.include_router(
        admin_router,
        prefix="/api/admin",
        tags=["admin"],
        dependencies=[Depends(require_admin)],
    )


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(FieldNotFoundException, field_not_found_exception_handler)
    app.add_exception_handler(
        DuplicateEntryException, duplicate_entry_exception_handler
    )
    app.add_exception_handler(CredentialsException, credentials_exception_handler)
    app.add_exception_handler(BadRequestException, bad_request_exception_handler)


async def create_initial_admin(db: AsyncSession):
    result = await db.execute(select(User).where(User.role == Role.ADMIN).limit(1))
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        return

    admin = User(
        first_name=settings.ADMIN_FIRST_NAME,
        last_name=settings.ADMIN_LAST_NAME,
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password=hash_password(settings.ADMIN_PASSWORD),
        role=Role.ADMIN,
    )

    db.add(admin)
    await db.commit()


def create_lifespan(test_mode: bool = False):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if test_mode:
            app.state.redis = None
            yield
            return

        from app.core.database import engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            try:
                await create_initial_admin(db)
            except Exception:
                await db.rollback()
                raise

        app.state.redis = None
        logger.info("App started (using asyncio for background tasks)")

        yield

        await engine.dispose()

    return lifespan


# Default lifespan for production
lifespan = create_lifespan(test_mode=False)


def setup_main(app: FastAPI):
    register_routers(app)
    register_exception_handlers(app)
