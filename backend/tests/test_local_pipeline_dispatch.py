from __future__ import annotations

from types import SimpleNamespace

from app.llm import summarize
from app.services import enrich, geocode


def test_step2_uses_local_llm_when_configured(monkeypatch) -> None:
    settings = SimpleNamespace(
        llm_local_provider="ollama",
        llm_local_base_url="http://127.0.0.1:11434",
        llm_local_model="qwen2.5:7b",
        llm_local_timeout_seconds=30,
        openai_api_key="",
        openai_api_base_url="",
        use_local_models_only=True,
        llm_timeout_seconds=30,
        llm_gap_fill_model="gpt-4o",
    )

    monkeypatch.setattr(enrich, "get_settings", lambda: settings)
    monkeypatch.setattr(enrich, "is_local_llm_configured", lambda *_: True)

    def _fake_call_local_llm(**kwargs):
        return (
            {
                "street_line": "3400 W Plano Pkwy",
                "city": "Plano",
                "state": "TX",
                "postal_code": "75075",
                "country": "US",
            },
            0,
            0,
            "qwen2.5:7b",
        )

    monkeypatch.setattr(enrich, "call_local_llm", _fake_call_local_llm)

    components = {"street_line": None, "city": None, "state": None, "postal_code": None, "country": None}
    merged, pt, ct, cost, provider = enrich.run_step2("3400 W Plano Pkwy Plano TX", components)

    assert merged["city"] == "Plano"
    assert provider == "qwen2.5:7b"
    assert pt == 0
    assert ct == 0
    assert cost == 0.0


def test_step4_local_only_skips_remote_geocoders(monkeypatch) -> None:
    settings = SimpleNamespace(
        geocoder_provider="none",
        geocoder_base_url="",
        geocoder_timeout_seconds=10,
        use_local_models_only=True,
        openai_api_key="dummy-key",
        openai_api_base_url="http://remote.example",
        llm_timeout_seconds=10,
        llm_search_model="gpt-4o-search-preview",
        serper_api_key="dummy-serper",
        serper_timeout_seconds=10,
        serper_api_base_url="https://api.serper.dev",
    )

    monkeypatch.setattr(geocode, "get_settings", lambda: settings)

    def _fail_remote(*args, **kwargs):
        raise AssertionError("remote geocoder should not be called in local-only mode")

    monkeypatch.setattr(geocode, "_geocode_via_llm", _fail_remote)
    monkeypatch.setattr(geocode, "_geocode_via_serper", _fail_remote)

    lat, lon, payload, backfill, pt, ct, cost, provider = geocode.run_step4(
        "3400 W Plano Pkwy, Plano, TX 75075", {"city": "Plano"}
    )

    assert lat is None
    assert lon is None
    assert payload == {}
    assert backfill == {}
    assert pt == 0
    assert ct == 0
    assert cost == 0.0
    assert provider == "stub"


def test_summary_local_only_without_local_provider_uses_rule_based(monkeypatch) -> None:
    settings = SimpleNamespace(
        llm_local_base_url="",
        llm_local_model="",
        openai_api_key="",
        openai_api_base_url="",
        use_local_models_only=True,
        llm_gap_fill_model="gpt-4o",
        llm_timeout_seconds=30,
        llm_local_provider="ollama",
        llm_local_timeout_seconds=30,
    )
    monkeypatch.setattr(summarize, "get_settings", lambda: settings)
    monkeypatch.setattr(summarize, "is_local_llm_configured", lambda *_: False)

    label, pt, ct = summarize.score_confidence(
        raw_address="3400 W Plano Pkwy Plano TX",
        parsed_components={"street_line": "3400 W Plano Pkwy"},
        enriched_components={
            "street_line": "3400 W Plano Pkwy",
            "city": "Plano",
            "state": "TX",
            "postal_code": "75075",
        },
        has_geocode=True,
    )

    summary_text = summarize.generate_summary(
        raw_address="3400 W Plano Pkwy Plano TX",
        parsed_components={"street_line": "3400 W Plano Pkwy"},
        enriched_components={
            "street_line": "3400 W Plano Pkwy",
            "city": "Plano",
            "state": "TX",
            "postal_code": "75075",
        },
        lat=33.0,
        lon=-96.0,
        confidence_label=label,
        steps_ran=[1, 2, 3, 4],
    )

    assert label == "high"
    assert pt == 0
    assert ct == 0
    assert "Enrichment pipeline ran" in summary_text
