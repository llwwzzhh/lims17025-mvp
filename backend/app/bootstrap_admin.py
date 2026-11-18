"""Create the initial administrator account interactively.

Run inside the backend container: python -m app.bootstrap_admin
"""

import asyncio
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db import SessionLocal
from app.models import Base
from app.db import engine
from app.models.identity import Role, User


async def main() -> None:
    username = input("Admin username: ").strip()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        if await session.scalar(select(User).where(User.username == username)):
            raise SystemExit("Username already exists")
        role = await session.scalar(select(Role).where(Role.key == "admin"))
        if role is None:
            role = Role(key="admin", name="系统管理员", permissions=["*"])
            session.add(role)
            await session.flush()
        session.add(User(username=username, full_name=full_name, password_hash=hash_password(password), roles=[role]))
        await session.commit()
    await engine.dispose()
    print("Administrator created. Store credentials securely.")


if __name__ == "__main__":
    asyncio.run(main())
