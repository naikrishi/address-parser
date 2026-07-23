from app.db.session import SessionLocal
from app.models.enrichment_result import EnrichmentResult
from app.models.geocode_result import GeocodeResult
from app.models.parse_result import ParseResult
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


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
    payload = {
        "raw_address": "3400 W Plano Pkwy, Plano, TX 75075, USA",
        "input_source": "swagger",
        "country_hint": "US",
    }

    response = client.post("/parse", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["parser_name"] == "stub"
    assert body["raw_input"]["raw_address"] == payload["raw_address"]


def test_post_parse_rejects_blank_raw_address() -> None:
    payload = {
        "raw_address": "   ",
        "input_source": "swagger",
    }

    response = client.post("/parse", json=payload)

    assert response.status_code == 422


def test_get_parse_by_id_returns_created_record() -> None:
    payload = {
        "raw_address": "1600 Amphitheatre Parkway, Mountain View, CA 94043, USA",
        "input_source": "swagger",
    }
    create_response = client.post("/parse", json=payload)
    assert create_response.status_code == 201

    parse_id = create_response.json()["id"]
    get_response = client.get(f"/parse/{parse_id}")

    assert get_response.status_code == 200
    body = get_response.json()
    assert body["id"] == parse_id
    assert body["raw_input"]["raw_address"] == payload["raw_address"]
    assert body["enrichment_results"] == []
    assert body["geocode_results"] == []


def test_get_parse_by_id_not_found() -> None:
    response = client.get("/parse/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["detail"] == "Parse result not found"


def test_get_inputs_returns_paginated_object() -> None:
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
        create_response = client.post("/parse", json=payload)
        assert create_response.status_code == 201
        created_ids.append(create_response.json()["raw_input_id"])

    list_response = client.get("/inputs", params={"limit": 10, "offset": 0})

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
    create_response = client.post(
        "/parse",
        json={
            "raw_address": "500 Example Ave, Plano, TX 75074, USA",
            "input_source": "integration",
        },
    )
    assert create_response.status_code == 201

    parse_id = create_response.json()["id"]
    seed_downstream_results(
        parse_id,
        enrichment_statuses=["partial", "complete"],
        geocode_statuses=["matched", "fallback"],
    )

    response = client.get(f"/parse/{parse_id}")

    assert response.status_code == 200
    body = response.json()
    assert [item["status"] for item in body["enrichment_results"]] == ["partial", "complete"]
    assert [item["status"] for item in body["geocode_results"]] == ["matched", "fallback"]


def test_get_parses_filters_on_downstream_presence() -> None:
    enriched_response = client.post(
        "/parse",
        json={
            "raw_address": "42 Rich Query Rd, Plano, TX 75024, USA",
            "input_source": "filter-test",
        },
    )
    plain_response = client.post(
        "/parse",
        json={
            "raw_address": "99 Plain Query Rd, Plano, TX 75024, USA",
            "input_source": "filter-test",
        },
    )
    assert enriched_response.status_code == 201
    assert plain_response.status_code == 201

    seed_downstream_results(
        enriched_response.json()["id"],
        enrichment_statuses=["complete"],
        geocode_statuses=["matched"],
    )

    response = client.get("/parses", params={"has_enrichment": True, "has_geocode": True})

    assert response.status_code == 200
    body = response.json()
    returned_parse_ids = {item["id"] for item in body["items"]}
    assert enriched_response.json()["id"] in returned_parse_ids
    assert plain_response.json()["id"] not in returned_parse_ids


def test_get_inputs_filters_on_downstream_presence() -> None:
    enriched_response = client.post(
        "/parse",
        json={
            "raw_address": "700 Filter Ln, Plano, TX 75023, USA",
            "input_source": "inputs-filter",
            "country_hint": "US",
        },
    )
    plain_response = client.post(
        "/parse",
        json={
            "raw_address": "701 Filter Ln, Plano, TX 75023, USA",
            "input_source": "inputs-filter",
            "country_hint": "US",
        },
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
