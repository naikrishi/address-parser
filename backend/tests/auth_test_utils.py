from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings


def unique_identity(prefix: str) -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    return (f"{prefix}_{suffix}@example.com", f"{prefix}_{suffix}")


def register_and_login(
    client: TestClient,
    *,
    prefix: str,
    role: str = "admin",
    password: str = "S3curePassw0rd",
) -> dict[str, str]:
    email, username = unique_identity(prefix)
    register_payload = {
        "email": email,
        "username": username,
        "password": password,
        "role": role,
    }

    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201, register_response.text
    user = register_response.json()

    login_response = client.post(
        "/auth/token",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200, login_response.text

    tokens = login_response.json()
    return {
        "user_id": user["id"],
        "email": email,
        "username": username,
        "password": password,
        "role": role,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def create_signed_token(payload: dict[str, Any], *, expires_in: timedelta) -> str:
    settings = get_settings()
    token_payload = {
        **payload,
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jwt.encode(token_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_expired_access_token(*, subject: str, role: str = "admin") -> str:
    return create_signed_token(
        {
            "sub": subject,
            "role": role,
            "type": "access",
        },
        expires_in=timedelta(minutes=-1),
    )


def create_expired_refresh_token(*, subject: str) -> str:
    return create_signed_token(
        {
            "sub": subject,
            "type": "refresh",
        },
        expires_in=timedelta(minutes=-1),
    )


def create_malformed_token() -> str:
    return "not-a-jwt"