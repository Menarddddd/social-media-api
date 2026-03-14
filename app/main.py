from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        yield

        await engine.dispose()


app = FastAPI(lifespan=lifespan)


@app.get("/", status_code=200)
async def test():
    return {"message": "test"}
