from fastapi.testclient import TestClient
from uuid import uuid4

from main import app


client = TestClient(app)


def _unique_identity(prefix: str) -> tuple[str, str]:
    suffix = uuid4().hex[:10]
    return (f"{prefix}_{suffix}@example.com", f"{prefix}_{suffix}")


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
    email, username = _unique_identity("week3_refresh")
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
        json={"username": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200, login_response.text

    access_token = login_response.json()["access_token"]
    refresh_response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert refresh_response.status_code == 401
