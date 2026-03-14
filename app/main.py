from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app import models
from app.routers.user import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        yield

        await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(user_router, prefix="/api/users", tags=["users"])
