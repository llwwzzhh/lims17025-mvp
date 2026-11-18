"""Liveness and readiness endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.core.config import settings
from app.db import engine
from app.models import Base
from app.models.identity import Role
from app.db import SessionLocal

DEFAULT_ROLES = [
    ("admin", "系统管理员", ["*"]),
    ("quality_manager", "质量负责人", ["users.read", "documents.manage", "nonconformities.manage", "audit.read"]),
    ("technical_reviewer", "技术审核人", ["users.read", "tasks.review", "reports.review"]),
    ("report_approver", "报告批准人", ["reports.approve"]),
    ("technician", "检测人员", ["samples.read", "tasks.execute", "data.record"]),
    ("sample_manager", "样品管理员", ["samples.manage"]),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Convenience for the initial MVP. Production deployments should use reviewed migrations.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        for key, name, permissions in DEFAULT_ROLES:
            if await session.scalar(__import__("sqlalchemy").select(Role).where(Role.key == key)) is None:
                session.add(Role(key=key, name=name, permissions=permissions))
        await session.commit()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

from app.api.identity import router as identity_router
app.include_router(identity_router)


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
