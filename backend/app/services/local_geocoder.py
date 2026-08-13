"""Local geocoder adapter (Nominatim-compatible).

Provides a contract-compatible payload for Step 4:
- latitude
- longitude
- nearby_businesses
"""

from __future__ import annotations

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def geocode_with_nominatim(
    *,
    base_url: str,
    timeout_seconds: int,
    address_str: str,
) -> tuple[dict, int, int, str]:
    """Return (payload, prompt_tokens, completion_tokens, provider_name)."""
    with httpx.Client(timeout=timeout_seconds) as client:
        search_resp = client.get(
            f"{base_url.rstrip('/')}/search",
            params={
                "q": address_str,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
            },
            headers={"User-Agent": "address-parser-local-geocoder/1.0"},
        )
        search_resp.raise_for_status()
        rows = search_resp.json()

        if not rows:
            return {"latitude": None, "longitude": None, "nearby_businesses": []}, 0, 0, "nominatim"

        first = rows[0]
        lat = _to_float(first.get("lat"))
        lon = _to_float(first.get("lon"))

        nearby_businesses = []
        if lat is not None and lon is not None:
            rev_resp = client.get(
                f"{base_url.rstrip('/')}/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "jsonv2",
                    "addressdetails": 1,
                },
                headers={"User-Agent": "address-parser-local-geocoder/1.0"},
            )
            rev_resp.raise_for_status()
            rev = rev_resp.json()
            display_name = rev.get("display_name") or first.get("display_name")
            if display_name:
                nearby_businesses.append(
                    {
                        "name": rev.get("name") or "Nearest Place",
                        "address": display_name,
                        "lat": lat,
                        "lon": lon,
                    }
                )

        payload = {
            "latitude": lat,
            "longitude": lon,
            "nearby_businesses": nearby_businesses,
        }
        return payload, 0, 0, "nominatim"


def _to_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
