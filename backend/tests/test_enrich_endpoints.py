"""Integration tests for Day 10: POST /enrich and GET /parse/{id}/summary."""
from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app
from tests.auth_test_utils import (
    auth_headers,
    create_expired_access_token,
    create_malformed_token,
    register_and_login,
)

client = TestClient(app)

def _auth_headers(prefix: str = "week3_enrich", role: str = "admin") -> dict[str, str]:
    suffix = uuid4().hex[:10]
    register_payload = {
        "email": f"{prefix}_{suffix}@example.com",
        "username": f"{prefix}_{suffix}",
        "password": "S3curePassw0rd",
        "role": role,
    }
    register_response = client.post("/auth/register", json=register_payload)
    assert register_response.status_code == 201, register_response.text

    login_response = client.post(
        "/auth/token",
        json={"username": register_payload["username"], "password": register_payload["password"]},
    )
    assert login_response.status_code == 200, login_response.text
    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parse(headers: dict[str, str], address: str = "3400 W Plano Pkwy, Plano, TX 75075, USA") -> dict:
    resp = client.post("/parse", json={"raw_address": address, "input_source": "test"}, headers=headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _stub_embed(raw_address, components):
    return [0.0] * 384


# ---------------------------------------------------------------------------
# POST /enrich — happy path (no LLM, everything falls through to stubs)
# ---------------------------------------------------------------------------

@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_post_enrich_creates_enrichment_and_geocode(mock_embed) -> None:
    admin_headers = _auth_headers("enrich_create_admin", role="admin")
    parse = _make_parse(admin_headers)
    resp = client.post("/enrich", json={"parse_result_id": parse["id"]}, headers=admin_headers)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["parse_result_id"] == parse["id"]
    assert body["enrichment_result_id"]
    assert "steps" in body
    assert len(body["steps"]) == 4
    assert body["total_estimated_cost"] >= 0.0


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_post_enrich_step_trace_has_four_steps(mock_embed) -> None:
    admin_headers = _auth_headers("enrich_steps_admin", role="admin")
    parse = _make_parse(admin_headers)
    resp = client.post("/enrich", json={"parse_result_id": parse["id"]}, headers=admin_headers)
    assert resp.status_code == 201
    steps = resp.json()["steps"]
    assert [s["step"] for s in steps] == [1, 2, 3, 4]


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_post_enrich_confidence_label_present(mock_embed) -> None:
    admin_headers = _auth_headers("enrich_confidence_admin", role="admin")
    parse = _make_parse(admin_headers)
    resp = client.post("/enrich", json={"parse_result_id": parse["id"]}, headers=admin_headers)
    assert resp.status_code == 201
    label = resp.json()["confidence_label"]
    assert label in ("low", "medium", "high")


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_post_enrich_404_for_unknown_parse_id(mock_embed) -> None:
    headers = _auth_headers("enrich_not_found_admin", role="admin")
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.post("/enrich", json={"parse_result_id": fake_id}, headers=headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /parse/{id}/summary
# ---------------------------------------------------------------------------

@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_get_summary_after_enrich_returns_cached(mock_embed) -> None:
    admin_headers = _auth_headers("summary_cached_admin", role="admin")
    ops_headers = _auth_headers("summary_cached_ops", role="ops")
    parse = _make_parse(admin_headers)
    enrich_resp = client.post("/enrich", json={"parse_result_id": parse["id"]}, headers=admin_headers)
    assert enrich_resp.status_code == 201

    summary_resp = client.get(f"/parse/{parse['id']}/summary", headers=ops_headers)
    assert summary_resp.status_code == 200
    body = summary_resp.json()
    assert body["parse_result_id"] == parse["id"]
    assert isinstance(body["summary"], str) and len(body["summary"]) > 0
    assert body["confidence_label"] in ("low", "medium", "high", None)


def test_get_summary_without_enrich_generates_stub() -> None:
    admin_headers = _auth_headers("summary_stub_admin", role="admin")
    ops_headers = _auth_headers("summary_stub_ops", role="ops")
    parse = _make_parse(admin_headers, "1 Microsoft Way, Redmond, WA 98052, US")
    resp = client.get(f"/parse/{parse['id']}/summary", headers=ops_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["parse_result_id"] == parse["id"]
    assert isinstance(body["summary"], str)


def test_get_summary_404_for_unknown_parse_id() -> None:
    headers = _auth_headers("summary_not_found_ops", role="ops")
    resp = client.get("/parse/00000000-0000-0000-0000-000000000000/summary", headers=headers)
    assert resp.status_code == 404


def test_enrich_and_summary_require_authentication() -> None:
    response = client.post("/enrich", json={"parse_result_id": "00000000-0000-0000-0000-000000000000"})
    assert response.status_code == 403

    response = client.get("/parse/00000000-0000-0000-0000-000000000000/summary")
    assert response.status_code == 403


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_ops_user_cannot_run_enrich(mock_embed) -> None:
    admin_headers = _auth_headers("enrich_ops_forbidden_admin", role="admin")
    ops_headers = _auth_headers("enrich_ops_forbidden_ops", role="ops")
    parse = _make_parse(admin_headers)

    response = client.post("/enrich", json={"parse_result_id": parse["id"]}, headers=ops_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_enrich_rejects_malformed_token(mock_embed) -> None:
    response = client.post(
        "/enrich",
        json={"parse_result_id": "00000000-0000-0000-0000-000000000000"},
        headers=auth_headers(create_malformed_token()),
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@patch("app.api.routers.enrich.embed_text", side_effect=_stub_embed)
def test_enrich_rejects_expired_token(mock_embed) -> None:
    identity = register_and_login(client, prefix="enrich_expired_token", role="admin")
    expired_headers = auth_headers(create_expired_access_token(subject=identity["user_id"], role="admin"))
    response = client.post(
        "/enrich",
        json={"parse_result_id": "00000000-0000-0000-0000-000000000000"},
        headers=expired_headers,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


# ---------------------------------------------------------------------------
# Cost estimator unit
# ---------------------------------------------------------------------------

def test_cost_estimator_zero_tokens() -> None:
    from app.services.cost import estimate_cost
    assert estimate_cost(0, 0) == 0.0


def test_cost_estimator_1k_tokens() -> None:
    from app.services.cost import estimate_cost
    # 1000 input + 1000 output with default GPT-4o pricing
    cost = estimate_cost(1000, 1000)
    assert 0.019 < cost < 0.021  # 0.005 + 0.015 = 0.020


def test_cost_estimator_result_rounded() -> None:
    from app.services.cost import estimate_cost
    cost = estimate_cost(333, 777)
    assert cost == round(cost, 6)


# ---------------------------------------------------------------------------
# Confidence scoring (rule-based fallback path)
# ---------------------------------------------------------------------------

def test_rule_based_high_confidence() -> None:
    from app.llm.summarize import _rule_based_confidence
    components = {"street_line": "3400 W Plano Pkwy", "city": "Plano", "state": "TX", "postal_code": "75075"}
    assert _rule_based_confidence(components, has_geocode=True) == "high"


def test_rule_based_low_confidence() -> None:
    from app.llm.summarize import _rule_based_confidence
    assert _rule_based_confidence({}, has_geocode=False) == "low"
