"""LLM-based enrichment summary and confidence scoring.

Uses local LLM configuration first when available. When neither local nor remote
providers are configured, both functions fall back to deterministic rule-based
outputs so the pipeline can run without external dependencies.
"""

from __future__ import annotations

import json
import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.llm.local_llm import call_local_llm, is_local_llm_configured

logger = logging.getLogger(__name__)

_CONFIDENCE_PROMPT = """\
You are evaluating the quality of an address enrichment result.

Original raw address: {raw_address}
Parsed components: {parsed_components}
Enriched components: {enriched_components}
Geocode available: {has_geocode}

Return ONLY a JSON object with two keys:
- "confidence": one of "low", "medium", or "high"
- "rationale": one short sentence explaining the rating

Criteria:
- high: all key fields present (street, city, state, postal_code), coordinates available
- medium: most fields present but one missing or geocode unavailable
- low: multiple fields missing, conflicting data, or geocode failed
"""

_SUMMARY_PROMPT = """\
Summarize in 2-3 sentences the enrichment pipeline result for the following address,
written for a technical operations audience. Include which steps ran, what was filled,
and whether the result is high confidence.

Raw address: {raw_address}
Parsed: {parsed_components}
Enriched: {enriched_components}
Geocode lat/lon: {lat_lon}
Confidence: {confidence_label}
Steps that ran: {steps_ran}
"""


def _llm_available() -> bool:
    s = get_settings()
    if is_local_llm_configured(s.llm_local_base_url, s.llm_local_model):
        return True
    return bool(s.openai_api_key and s.openai_api_base_url)


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_llm(prompt: str, max_tokens: int = 256) -> tuple[str, int, int]:
    """Return (response_text, prompt_tokens, completion_tokens)."""
    settings = get_settings()

    if is_local_llm_configured(settings.llm_local_base_url, settings.llm_local_model):
        parsed_json, pt, ct, _ = call_local_llm(
            provider=settings.llm_local_provider,
            base_url=settings.llm_local_base_url,
            model=settings.llm_local_model,
            prompt=prompt,
            max_tokens=max_tokens,
            timeout_seconds=settings.llm_local_timeout_seconds,
        )
        return json.dumps(parsed_json), pt, ct

    if settings.use_local_models_only:
        raise RuntimeError("Local-only mode enabled but local LLM is not configured")

    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        resp = client.post(
            f"{settings.openai_api_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.llm_gap_fill_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content: str = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return content, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def score_confidence(
    raw_address: str,
    parsed_components: dict,
    enriched_components: dict,
    has_geocode: bool,
) -> tuple[str, int, int]:
    """Return (confidence_label, prompt_tokens, completion_tokens).

    Falls back to a rule-based label when LLM is unavailable.
    """
    if not _llm_available():
        label = _rule_based_confidence(enriched_components, has_geocode)
        return label, 0, 0

    prompt = _CONFIDENCE_PROMPT.format(
        raw_address=raw_address,
        parsed_components=json.dumps(parsed_components),
        enriched_components=json.dumps(enriched_components),
        has_geocode=has_geocode,
    )
    try:
        text, pt, ct = _call_llm(prompt, max_tokens=100)
        data = json.loads(text.strip())
        label = data.get("confidence", "medium")
        if label not in ("low", "medium", "high"):
            label = "medium"
        return label, pt, ct
    except Exception as exc:
        logger.warning("Confidence LLM call failed (%s); using rule-based fallback", exc)
        label = _rule_based_confidence(enriched_components, has_geocode)
        return label, 0, 0


def _rule_based_confidence(enriched_components: dict, has_geocode: bool) -> str:
    required = ["street_line", "city", "state", "postal_code"]
    filled = sum(1 for k in required if enriched_components.get(k))
    if filled == 4 and has_geocode:
        return "high"
    if filled >= 3:
        return "medium"
    return "low"


def generate_summary(
    raw_address: str,
    parsed_components: dict,
    enriched_components: dict,
    lat: float | None,
    lon: float | None,
    confidence_label: str,
    steps_ran: list[int],
) -> str:
    """Return a plain-text summary of the enrichment path."""
    if not _llm_available():
        return _rule_based_summary(raw_address, enriched_components, lat, lon, confidence_label, steps_ran)

    lat_lon = f"{lat}, {lon}" if lat is not None and lon is not None else "unavailable"
    prompt = _SUMMARY_PROMPT.format(
        raw_address=raw_address,
        parsed_components=json.dumps(parsed_components),
        enriched_components=json.dumps(enriched_components),
        lat_lon=lat_lon,
        confidence_label=confidence_label,
        steps_ran=", ".join(f"Step {s}" for s in steps_ran),
    )
    try:
        text, _, _ = _call_llm(prompt, max_tokens=200)
        return text.strip()
    except Exception as exc:
        logger.warning("Summary LLM call failed (%s); using rule-based summary", exc)
        return _rule_based_summary(raw_address, enriched_components, lat, lon, confidence_label, steps_ran)


def _rule_based_summary(
    raw_address: str,
    enriched_components: dict,
    lat: float | None,
    lon: float | None,
    confidence_label: str,
    steps_ran: list[int],
) -> str:
    steps_str = ", ".join(f"Step {s}" for s in steps_ran) if steps_ran else "Step 1 only"
    geocode_str = f"lat={lat}, lon={lon}" if lat is not None else "no geocode"
    filled = [k for k in ("street_line", "city", "state", "postal_code") if enriched_components.get(k)]
    return (
        f'Enrichment pipeline ran {steps_str} for "{raw_address}". '
        f"Fields resolved: {', '.join(filled) or 'none'}. "
        f"Geocode: {geocode_str}. Confidence: {confidence_label}."
    )

