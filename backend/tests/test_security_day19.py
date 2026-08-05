from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.routers.auth import login_rate_limiter
from app.db.session import SessionLocal
from app.models.audit_event import AuditEvent
from main import app

client = TestClient(app)


def _register_user(prefix: str, role: str = "admin") -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    email = f"{prefix}_{suffix}@example.com"
    username = f"{prefix}_{suffix}"
    payload = {
        "email": email,
        "username": username,
        "password": "S3curePassw0rd",
        "role": role,
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return username, payload["password"]


def _auth_headers(prefix: str, role: str = "admin") -> dict[str, str]:
    username, password = _register_user(prefix, role=role)
    response = client.post("/auth/token", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_rate_limit_returns_429_after_threshold() -> None:
    username, password = _register_user("rate_limit")

    original_limit = login_rate_limiter.limit
    original_hits = login_rate_limiter._hits
    login_rate_limiter.limit = 2
    login_rate_limiter._hits = {}

    try:
        first = client.post("/auth/token", json={"username": username, "password": password})
        second = client.post("/auth/token", json={"username": username, "password": password})
        third = client.post("/auth/token", json={"username": username, "password": password})

        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert third.status_code == 429, third.text
        assert "Too many login attempts" in third.json()["detail"]
    finally:
        login_rate_limiter.limit = original_limit
        login_rate_limiter._hits = original_hits


@patch("app.api.routers.enrich.embed_text", side_effect=lambda *_args, **_kwargs: [0.0] * 384)
def test_audit_events_created_for_parse_and_enrich(_mock_embed) -> None:
    headers = _auth_headers("audit_event_user", role="admin")

    parse_response = client.post(
        "/parse",
        json={"raw_address": "3400 W Plano Pkwy, Plano, TX 75075, USA", "input_source": "audit-test"},
        headers=headers,
    )
    assert parse_response.status_code == 201, parse_response.text

    parse_id = parse_response.json()["id"]
    enrich_response = client.post("/enrich", json={"parse_result_id": parse_id}, headers=headers)
    assert enrich_response.status_code == 201, enrich_response.text

    with SessionLocal() as session:
        events = session.scalars(
            select(AuditEvent)
            .where(AuditEvent.action.in_(["parse.create", "enrich.run"]))
            .order_by(AuditEvent.created_at.desc())
            .limit(6)
        ).all()

    actions = {event.action for event in events}
    assert "parse.create" in actions
    assert "enrich.run" in actions

    parse_events = [event for event in events if event.action == "parse.create"]
    assert parse_events
    assert parse_events[0].raw_address_redacted is not None
    assert "3400" not in parse_events[0].raw_address_redacted
