"""Liveness and readiness endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.db import engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ready"}
