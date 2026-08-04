"""Step 1: address parsing service.

Wraps the existing stub parser (comma-split heuristic). When libpostal is
available in the environment, replace _libpostal_parse with a real call.
"""

from __future__ import annotations

REQUIRED_COMPONENT_KEYS = ["street_line", "city", "state", "postal_code"]


def parse_address(raw_address: str, country_hint: str | None) -> tuple[dict[str, str | None], bool, float]:
    """Return (parsed_components, is_complete, confidence_score)."""
    components = _libpostal_parse(raw_address, country_hint)
    complete = all(components.get(k) for k in REQUIRED_COMPONENT_KEYS)
    confidence = 0.75 if complete else 0.4
    return components, complete, confidence


def _libpostal_parse(raw_address: str, country_hint: str | None) -> dict[str, str | None]:
    # PLACEHOLDER: replace with `postal.parse_address(raw_address)` once libpostal is installed
    parts = [s.strip() for s in raw_address.split(",") if s.strip()]
    street_line = parts[0] if parts else None
    city = parts[1] if len(parts) > 1 else None
    state = postal_code = None
    if len(parts) > 2:
        tokens = parts[2].split()
        state = tokens[0] if tokens else None
        postal_code = tokens[-1] if len(tokens) > 1 else None
    country = country_hint or (parts[3] if len(parts) > 3 else None)
    return {
        "street_line": street_line,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "country": country,
    }
