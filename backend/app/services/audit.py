from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.user import User


def redact_address(raw_address: str) -> str:
    # Redact street numbers while keeping non-sensitive locality context.
    return re.sub(r"\b\d+\b", "***", raw_address)


def record_audit_event(
    db: Session,
    *,
    user: User,
    action: str,
    resource_type: str,
    resource_id: str | None,
    raw_address: str | None,
) -> None:
    event = AuditEvent(
        user_id=user.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        raw_address_redacted=redact_address(raw_address) if raw_address else None,
    )
    db.add(event)
