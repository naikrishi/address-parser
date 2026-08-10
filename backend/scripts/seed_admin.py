from __future__ import annotations

import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def seed_admin_user() -> None:
    username = _env("SEED_ADMIN_USERNAME", "admin")
    email = _env("SEED_ADMIN_EMAIL", "admin@example.com").lower()
    password = _env("SEED_ADMIN_PASSWORD", "admin12345")

    if not username or not email or not password:
        raise ValueError("Seed admin username/email/password must be non-empty")

    with SessionLocal() as session:
        existing = session.scalar(
            select(User).where((User.username == username) | (User.email == email))
        )
        if existing is not None:
            if existing.username != username:
                existing.username = username
            if existing.email != email:
                existing.email = email
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
            if not existing.is_active:
                existing.is_active = True
            session.commit()
            return

        session.add(
            User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        session.commit()


if __name__ == "__main__":
    seed_admin_user()