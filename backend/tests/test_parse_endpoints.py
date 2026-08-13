from app.db.session import SessionLocal
from app.models.enrichment_result import EnrichmentResult
from app.models.geocode_result import GeocodeResult
from app.models.parse_result import ParseResult
from fastapi.testclient import TestClient
from uuid import uuid4

from main import app
from tests.auth_test_utils import (
    auth_headers,
    create_expired_access_token,
    create_malformed_token,
    register_and_login,
)


client = TestClient(app)


def _auth_headers(prefix: str = "week3_parse", role: str = "admin") -> dict[str, str]:
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


def seed_downstream_results(
    parse_id: str,
    *,
    enrichment_statuses: list[str],
    geocode_statuses: list[str],
) -> None:
    with SessionLocal() as session:
        parse_result = session.get(ParseResult, parse_id)
        assert parse_result is not None

        enrichments: list[EnrichmentResult] = []
        for index, status in enumerate(enrichment_statuses, start=1):
            enrichment = EnrichmentResult(
                parse_result_id=parse_result.id,
                provider_name="llm-stub",
                status=status,
                enriched_components={
                    "street_line": f"{index} enriched street",
                    "city": "Plano",
                    "state": "TX",
                    "postal_code": "75075",
                },
                is_complete=status == "complete",
                confidence_score=0.55 + (index * 0.1),
            )
            session.add(enrichment)
            enrichments.append(enrichment)

        session.flush()

        for index, status in enumerate(geocode_statuses, start=1):
            enrichment = enrichments[min(index - 1, len(enrichments) - 1)] if enrichments else None
            session.add(
                GeocodeResult(
                    parse_result_id=parse_result.id,
                    enrichment_result_id=enrichment.id if enrichment is not None else None,
                    provider_name="geocoder-stub",
                    status=status,
                    latitude=32.9 + index,
                    longitude=-96.7 - index,
                    result_payload={"match_quality": "roof-top", "attempt": index},
                )
            )

        session.commit()


def test_post_parse_creates_record() -> None:
    headers = _auth_headers("parse_create", role="admin")
    payload = {
        "raw_address": "3400 W Plano Pkwy, Plano, TX 75075, USA",
        "input_source": "swagger",
        "country_hint": "US",
    }

    response = client.post("/parse", json=payload, headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["parser_name"] in {"usaddress", "heuristic"}
    assert body["raw_input"]["raw_address"] == payload["raw_address"]


def test_post_parse_rejects_blank_raw_address() -> None:
    headers = _auth_headers("parse_blank", role="admin")
    payload = {
        "raw_address": "   ",
        "input_source": "swagger",
    }

    response = client.post("/parse", json=payload, headers=headers)

    assert response.status_code == 422


def test_get_parse_by_id_returns_created_record() -> None:
    admin_headers = _auth_headers("parse_get_admin", role="admin")
    ops_headers = _auth_headers("parse_get_ops", role="ops")
    payload = {
        "raw_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
        "input_source": "swagger",
    }
    create_response = client.post("/parse", json=payload, headers=admin_headers)
    assert create_response.status_code == 201

    parse_id = create_response.json()["id"]
    get_response = client.get(f"/parse/{parse_id}", headers=ops_headers)

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["id"] == parse_id
    assert body["raw_input"]["raw_address"] == payload["raw_address"]
    assert body["enrichment_results"] == []
    assert body["geocode_results"] == []


def test_get_parse_by_id_not_found() -> None:
    headers = _auth_headers("parse_not_found", role="ops")
    response = client.get("/parse/00000000-0000-0000-0000-000000000000", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Parse result not found"


def test_get_inputs_returns_paginated_object() -> None:
    admin_headers = _auth_headers("inputs_paginated_admin", role="admin")
    ops_headers = _auth_headers("inputs_paginated_ops", role="ops")
    seed_payloads = [
        {
            "raw_address": "1 Microsoft Way, Redmond, WA 98052, USA",
            "input_source": "swagger",
        },
        {
            "raw_address": "221B Baker Street, London, NW1, UK",
            "input_source": "swagger",
        },
    ]

    created_ids: list[str] = []
    for payload in seed_payloads:
        create_response = client.post("/parse", json=payload, headers=admin_headers)
        assert create_response.status_code == 201
        created_ids.append(create_response.json()["raw_input_id"])

    list_response = client.get("/inputs", params={"limit": 10, "offset": 0}, headers=ops_headers)

    assert list_response.status_code == 200
    body = list_response.json()
    assert set(body.keys()) == {"items", "total", "limit", "offset"}
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["total"] >= len(seed_payloads)

    returned_ids = {item["id"] for item in body["items"]}
    for created_id in created_ids:
        assert created_id in returned_ids


def test_get_parse_by_id_returns_downstream_results() -> None:
    admin_headers = _auth_headers("parse_downstream_admin", role="admin")
    ops_headers = _auth_headers("parse_downstream_ops", role="ops")
    create_response = client.post(
        "/parse",
        json={
            "raw_address": "500 Example Ave, Plano, TX 75074, USA",
            "input_source": "integration",
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201

    parse_id = create_response.json()["id"]
    seed_downstream_results(
        parse_id,
        enrichment_statuses=["partial", "complete"],
        geocode_statuses=["matched", "fallback"],
    )

    response = client.get(f"/parse/{parse_id}", headers=ops_headers)

    assert response.status_code == 200
    body = response.json()
    assert [item["status"] for item in body["enrichment_results"]] == ["partial", "complete"]
    assert [item["status"] for item in body["geocode_results"]] == ["matched", "fallback"]


def test_get_parses_filters_on_downstream_presence() -> None:
    admin_headers = _auth_headers("parses_filters_admin", role="admin")
    ops_headers = _auth_headers("parses_filters_ops", role="ops")
    enriched_response = client.post(
        "/parse",
        json={
            "raw_address": "42 Rich Query Rd, Plano, TX 75024, USA",
            "input_source": "filter-test",
        },
        headers=admin_headers,
    )
    plain_response = client.post(
        "/parse",
        json={
            "raw_address": "99 Plain Query Rd, Plano, TX 75024, USA",
            "input_source": "filter-test",
        },
        headers=admin_headers,
    )
    assert enriched_response.status_code == 201
    assert plain_response.status_code == 201

    seed_downstream_results(
        enriched_response.json()["id"],
        enrichment_statuses=["complete"],
        geocode_statuses=["matched"],
    )

    response = client.get("/parses", params={"has_enrichment": True, "has_geocode": True}, headers=ops_headers)

    assert response.status_code == 200
    body = response.json()
    returned_parse_ids = {item["id"] for item in body["items"]}
    assert enriched_response.json()["id"] in returned_parse_ids
    assert plain_response.json()["id"] not in returned_parse_ids


def test_get_inputs_filters_on_downstream_presence() -> None:
    admin_headers = _auth_headers("inputs_filters_admin", role="admin")
    ops_headers = _auth_headers("inputs_filters_ops", role="ops")
    enriched_response = client.post(
        "/parse",
        json={
            "raw_address": "700 Filter Ln, Plano, TX 75023, USA",
            "input_source": "inputs-filter",
            "country_hint": "US",
        },
        headers=admin_headers,
    )
    plain_response = client.post(
        "/parse",
        json={
            "raw_address": "701 Filter Ln, Plano, TX 75023, USA",
            "input_source": "inputs-filter",
            "country_hint": "US",
        },
        headers=admin_headers,
    )
    assert enriched_response.status_code == 201
    assert plain_response.status_code == 201

    seed_downstream_results(
        enriched_response.json()["id"],
        enrichment_statuses=["complete"],
        geocode_statuses=["matched"],
    )

    response = client.get(
        "/inputs",
        params={
            "input_source": "inputs-filter",
            "country_hint": "US",
            "has_enrichment": True,
            "has_geocode": True,
        },
        headers=ops_headers,
    )

    assert response.status_code == 200
    body = response.json()
    returned_input_ids = {item["id"] for item in body["items"]}
    assert enriched_response.json()["raw_input_id"] in returned_input_ids
    assert plain_response.json()["raw_input_id"] not in returned_input_ids

    enriched_item = next(item for item in body["items"] if item["id"] == enriched_response.json()["raw_input_id"])
    assert enriched_item["enrichment_result_count"] == 1
    assert enriched_item["geocode_result_count"] == 1
    assert enriched_item["has_enrichment"] is True
    assert enriched_item["has_geocode"] is True


def test_post_parse_accepts_null_country_hint() -> None:
    headers = _auth_headers("parse_country_hint", role="admin")
    response = client.post(
        "/parse",
        json={
            "raw_address": "742 Evergreen Terrace, Springfield, IL 62704",
            "input_source": "integration",
            "country_hint": None,
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["raw_input"]["country_hint"] is None


def test_parse_detail_contains_new_enrich_result_link() -> None:
    admin_headers = _auth_headers("parse_detail_link_admin", role="admin")
    ops_headers = _auth_headers("parse_detail_link_ops", role="ops")
    create_response = client.post(
        "/parse",
        json={
            "raw_address": "500 Oracle Pkwy, Redwood City, CA 94065, USA",
            "input_source": "integration",
            "country_hint": "US",
        },
        headers=admin_headers,
    )
    assert create_response.status_code == 201

    parse_id = create_response.json()["id"]
    seed_downstream_results(
        parse_id,
        enrichment_statuses=["complete"],
        geocode_statuses=["matched"],
    )

    detail_response = client.get(f"/parse/{parse_id}", headers=ops_headers)
    assert detail_response.status_code == 200
    detail = detail_response.json()

    assert len(detail["enrichment_results"]) >= 1
    assert len(detail["geocode_results"]) >= 1
    assert detail["enrichment_results"][-1]["parse_result_id"] == parse_id
    assert detail["geocode_results"][-1]["parse_result_id"] == parse_id


def test_parse_routes_require_authentication() -> None:
    response = client.get("/inputs")
    assert response.status_code == 403

    response = client.post(
        "/parse",
        json={"raw_address": "100 Main St, Plano, TX 75075", "input_source": "auth-check"},
    )
    assert response.status_code == 403


def test_ops_user_cannot_create_parse() -> None:
    ops_headers = _auth_headers("parse_ops_forbidden", role="ops")
    response = client.post(
        "/parse",
        json={"raw_address": "110 Main St, Plano, TX 75075", "input_source": "rbac-check"},
        headers=ops_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin role required"


def test_parse_routes_reject_malformed_token() -> None:
    headers = auth_headers(create_malformed_token())
    response = client.get("/inputs", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_parse_routes_reject_expired_token() -> None:
    identity = register_and_login(client, prefix="parse_expired_token", role="ops")
    headers = auth_headers(create_expired_access_token(subject=identity["user_id"], role="ops"))
    response = client.get("/inputs", headers=headers)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"
