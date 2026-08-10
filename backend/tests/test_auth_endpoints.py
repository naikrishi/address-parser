from fastapi.testclient import TestClient

from main import app
from tests.auth_test_utils import (
    auth_headers,
    create_expired_access_token,
    create_expired_refresh_token,
    create_malformed_token,
    register_and_login,
    unique_identity,
)


client = TestClient(app)


def _unique_identity(prefix: str) -> tuple[str, str]:
    return unique_identity(prefix)


def test_register_user_success() -> None:
    email, username = _unique_identity("week3_register_success")
    payload = {
        "email": email,
        "username": username,
        "password": "S3curePassw0rd",
        "role": "ops",
    }

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["role"] == payload["role"]
    assert body["is_active"] is True


def test_register_user_conflict_on_duplicate_email_or_username() -> None:
    email, username = _unique_identity("week3_duplicate")
    payload = {
        "email": email,
        "username": username,
        "password": "S3curePassw0rd",
        "role": "ops",
    }

    first_response = client.post("/auth/register", json=payload)
    assert first_response.status_code == 201, first_response.text

    second_response = client.post("/auth/register", json=payload)
    assert second_response.status_code == 409


def test_login_and_me_happy_path() -> None:
    email, username = _unique_identity("week3_login")
    register_payload = {
        "email": email,
        "username": username,
        "password": "S3curePassw0rd",
        "role": "admin",
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/auth/token",
        json={"username": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200, login_response.text
    tokens = login_response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]
    assert tokens["token_type"] == "bearer"

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me_response.status_code == 200, me_response.text
    body = me_response.json()
    assert body["user"]["email"] == register_payload["email"]
    assert body["user"]["role"] == "admin"


def test_login_rejects_wrong_password() -> None:
    email, username = _unique_identity("week3_wrong_password")
    register_payload = {
        "email": email,
        "username": username,
        "password": "S3curePassw0rd",
        "role": "ops",
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/auth/token",
        json={"username": register_payload["username"], "password": "WrongPassword123"},
    )
    assert login_response.status_code == 401


def test_refresh_rejects_non_refresh_token() -> None:
    identity = register_and_login(client, prefix="week3_refresh", role="ops")
    refresh_response = client.post("/auth/refresh", json={"refresh_token": identity["access_token"]})
    assert refresh_response.status_code == 401


def test_me_rejects_missing_token() -> None:
    response = client.get("/auth/me")
    assert response.status_code == 403


def test_me_rejects_malformed_token() -> None:
    response = client.get("/auth/me", headers=auth_headers(create_malformed_token()))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_me_rejects_expired_access_token() -> None:
    identity = register_and_login(client, prefix="week3_me_expired", role="admin")
    expired_token = create_expired_access_token(subject=identity["user_id"], role="admin")
    response = client.get("/auth/me", headers=auth_headers(expired_token))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_me_rejects_token_without_subject() -> None:
    token = create_signed_access_token_without_subject()
    response = client.get("/auth/me", headers=auth_headers(token))
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid access token"


def test_refresh_rejects_malformed_token() -> None:
    response = client.post("/auth/refresh", json={"refresh_token": create_malformed_token()})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_refresh_rejects_expired_refresh_token() -> None:
    identity = register_and_login(client, prefix="week3_refresh_expired", role="ops")
    expired_token = create_expired_refresh_token(subject=identity["user_id"])
    response = client.post("/auth/refresh", json={"refresh_token": expired_token})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def create_signed_access_token_without_subject() -> str:
    from datetime import timedelta

    from tests.auth_test_utils import create_signed_token

    return create_signed_token({"role": "admin", "type": "access"}, expires_in=timedelta(minutes=5))
