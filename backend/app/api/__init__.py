"""Authentication and user administration API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, current_user, hash_password, require_permission, verify_password
from app.db import get_db
from app.models.identity import AuditLog, Role, User
from app.schemas import LoginRequest, TokenView, UserCreate, UserView

router = APIRouter(prefix="/api", tags=["identity"])


def user_view(user: User) -> UserView:
    return UserView(id=user.id, username=user.username, full_name=user.full_name, is_active=user.is_active, roles=[role.key for role in user.roles])


@router.post("/auth/token", response_model=TokenView)
async def login(payload: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenView:
    user = await db.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    db.add(AuditLog(actor_user_id=user.id, action="auth.login", entity_type="user", entity_id=str(user.id), details={}))
    await db.commit()
    return TokenView(access_token=create_access_token(user.id))


@router.get("/auth/me", response_model=UserView)
async def me(user: Annotated[User, Depends(current_user)]) -> UserView:
    return user_view(user)


@router.post("/users", response_model=UserView, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    actor: Annotated[User, Depends(require_permission("users.manage"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserView:
    existing = await db.scalar(select(User).where(User.username == payload.username))
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    roles = list((await db.scalars(select(Role).where(Role.key.in_(payload.role_keys)))).all()) if payload.role_keys else []
    if len(roles) != len(set(payload.role_keys)):
        raise HTTPException(status_code=422, detail="One or more role keys are unknown")
    user = User(username=payload.username, full_name=payload.full_name, password_hash=hash_password(payload.password), roles=roles)
    db.add(user)
    await db.flush()
    db.add(AuditLog(actor_user_id=actor.id, action="user.create", entity_type="user", entity_id=str(user.id), details={"username": user.username, "roles": payload.role_keys}))
    await db.commit()
    await db.refresh(user)
    return user_view(user)


@router.get("/users", response_model=list[UserView])
async def list_users(
    _: Annotated[User, Depends(require_permission("users.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserView]:
    users = await db.scalars(select(User).order_by(User.id))
    return [user_view(user) for user in users]
