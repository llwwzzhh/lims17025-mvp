"""Liveness and readiness endpoints."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import select, text

from app.core.config import settings
from app.db import SessionLocal, engine
from app.models import Base
from app.models.identity import Role

DEFAULT_ROLES = [
    ("admin", "系统管理员", ["*"]),
    ("quality_manager", "质量负责人", ["users.read", "documents.manage", "documents.read", "documents.approve", "nonconformities.manage", "nonconformities.read", "audit.read", "contracts.read", "contracts.review", "samples.read", "equipment.read", "equipment.manage", "templates.read", "templates.manage", "tasks.read", "system_validation.manage", "system_validation.read", "system_validation.approve", "data.read"]),
    ("technical_reviewer", "技术审核人", ["users.read", "tasks.review", "reports.review", "reports.read", "contracts.read", "samples.read", "documents.read", "equipment.read", "templates.read", "tasks.read", "data.read"]),
    ("report_approver", "报告批准人", ["reports.approve", "reports.read"]),
    ("technician", "检测人员", ["samples.read", "tasks.execute", "tasks.read", "data.record", "contracts.read", "documents.read", "equipment.read", "templates.read"]),
    ("sample_manager", "样品管理员", ["samples.manage", "samples.read", "contracts.read"]),
]


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Development convenience only. Production deployments should use reviewed migrations.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        for key, name, permissions in DEFAULT_ROLES:
            role = await session.scalar(select(Role).where(Role.key == key))
            if role is None:
                session.add(Role(key=key, name=name, permissions=permissions))
            elif key != "admin":
                role.permissions = permissions
        await session.commit()
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

from app.api.identity import router as identity_router
from app.api.core import router as core_router
from app.api.quality import router as quality_router
app.include_router(identity_router)
app.include_router(core_router)
app.include_router(quality_router)


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
