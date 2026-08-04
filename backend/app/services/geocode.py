"""Step 4: geocoding — gpt-4o-search-preview primary, Serper Maps API fallback.

When neither is configured, a stub response is returned so the pipeline runs locally.
"""

from __future__ import annotations

import json
import logging
import re

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.services.cost import estimate_cost

logger = logging.getLogger(__name__)

_GEOCODE_PROMPT = """\
Find the latitude and longitude for the following address and return up to 5 nearby businesses.
Return ONLY a JSON object with keys:
- "latitude": float or null
- "longitude": float or null
- "nearby_businesses": list of objects each with "name", "address", "lat", "lon"

Address: {address}
"""


def _llm_available() -> bool:
    s = get_settings()
    return bool(s.openai_api_key and s.openai_api_base_url)


def _serper_available() -> bool:
    return bool(get_settings().serper_api_key)


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _geocode_via_llm(address_str: str) -> tuple[dict, int, int]:
    """Return (payload, prompt_tokens, completion_tokens)."""
    settings = get_settings()
    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        resp = client.post(
            f"{settings.openai_api_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.llm_search_model,
                "messages": [{"role": "user", "content": _GEOCODE_PROMPT.format(address=address_str)}],
                "max_tokens": 512,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return json.loads(content), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _geocode_via_serper(address_str: str) -> dict:
    """Return Serper places payload. PLACEHOLDER: adjust once key is issued."""
    settings = get_settings()
    with httpx.Client(timeout=settings.serper_timeout_seconds) as client:
        resp = client.post(
            f"{settings.serper_api_base_url}/maps",
            headers={"X-API-KEY": settings.serper_api_key},
            json={"q": address_str, "gl": "us"},
        )
        resp.raise_for_status()
        return resp.json()


def _parse_address_from_business(address_str: str) -> dict[str, str | None]:
    """Regex-extract city/state/postal from a business address string for backfill."""
    match = re.search(r",\s*([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", address_str)
    if match:
        return {"city": match.group(1).strip(), "state": match.group(2), "postal_code": match.group(3)}
    return {}


def run_step4(
    address_str: str, enriched_components: dict
) -> tuple[float | None, float | None, dict, dict, int, int, float, str]:
    """Geocode the address and optionally backfill missing fields from the first business result.

    Returns:
        (latitude, longitude, result_payload, backfill_components,
         prompt_tokens, completion_tokens, cost_usd, provider_name)
    """
    if _llm_available():
        try:
            payload, pt, ct = _geocode_via_llm(address_str)
            lat = payload.get("latitude")
            lon = payload.get("longitude")
            backfill = _extract_backfill(payload, enriched_components)
            cost = estimate_cost(pt, ct)
            return lat, lon, payload, backfill, pt, ct, cost, "gpt-4o-search-preview"
        except Exception as exc:
            logger.warning("LLM geocode failed (%s); trying Serper fallback", exc)

    if _serper_available():
        try:
            serper_data = _geocode_via_serper(address_str)
            places = serper_data.get("places", [])
            lat = lon = None
            payload: dict = {"nearby_businesses": []}
            if places:
                first = places[0]
                lat = first.get("lat") or first.get("latitude")
                lon = first.get("lon") or first.get("longitude") or first.get("lng")
                payload = {"nearby_businesses": places}
            backfill = _extract_backfill(payload, enriched_components)
            return lat, lon, payload, backfill, 0, 0, 0.0, "serper"
        except Exception as exc:
            logger.error("Serper geocode fallback also failed: %s", exc)

    logger.warning("No geocode provider available; returning stub")
    return None, None, {}, {}, 0, 0, 0.0, "stub"


def _extract_backfill(payload: dict, current_components: dict) -> dict[str, str | None]:
    """Return fields from nearest business address that fill gaps in current_components."""
    businesses = payload.get("nearby_businesses", [])
    if not businesses:
        return {}
    first_addr = businesses[0].get("address", "")
    extracted = _parse_address_from_business(first_addr)
    # Only backfill fields that are actually missing
    return {k: v for k, v in extracted.items() if not current_components.get(k)}
