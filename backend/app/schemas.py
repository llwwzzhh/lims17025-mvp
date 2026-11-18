"""Request schemas for identity endpoints."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    full_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role_keys: list[str] = Field(default_factory=list)


class UserView(BaseModel):
    id: int
    username: str
    full_name: str
    is_active: bool
    roles: list[str]


class TokenView(BaseModel):
    access_token: str
    token_type: str = "bearer"
