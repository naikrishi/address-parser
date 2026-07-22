from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


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
