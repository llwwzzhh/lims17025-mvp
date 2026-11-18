"""Record security-relevant administrative actions in the audit table."""

from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditLog


async def write_audit(
    db: AsyncSession,
    *,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> None:
    db.add(AuditLog(actor_user_id=actor_user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details or {}))
