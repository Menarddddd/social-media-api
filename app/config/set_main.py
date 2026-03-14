from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app import models

from app.exceptions.exception import (
    CredentialsException,
    DuplicateEntryException,
    FieldNotFoundException,
)
from app.exceptions.handler import (
    credentials_exception_handler,
    duplicate_entry_exception_handler,
    field_not_found_exception_handler,
)
from app.routers.user import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        yield

        await engine.dispose()


def register_routers(app: FastAPI):
    app.include_router(user_router, prefix="/api/users", tags=["users"])


def register_exception_handlers(app: FastAPI):
    app.add_exception_handler(FieldNotFoundException, field_not_found_exception_handler)
    app.add_exception_handler(
        DuplicateEntryException, duplicate_entry_exception_handler
    )
    app.add_exception_handler(CredentialsException, credentials_exception_handler)
