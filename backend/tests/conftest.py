from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal


@pytest.fixture(scope="session", autouse=True)
def require_database_connection() -> None:
    """Fail fast with a clear message when Postgres is unavailable for integration tests."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        pytest.exit(
            "Postgres is not reachable. Start it with 'docker compose up -d postgres' and retry tests. "
            f"Original error: {exc}",
            returncode=2,
        )
