"""Step 1: address parsing service.

Wraps the existing stub parser (comma-split heuristic). When libpostal is
available in the environment, replace _libpostal_parse with a real call.
"""

from __future__ import annotations

REQUIRED_COMPONENT_KEYS = ["street_line", "city", "state", "postal_code"]


def parse_address_with_provider(
    raw_address: str,
    country_hint: str | None,
) -> tuple[dict[str, str | None], bool, float, str]:
    """Return (parsed_components, is_complete, confidence_score, parser_name)."""
    components, parser_name = _parse_with_provider(raw_address, country_hint)
    complete = all(components.get(k) for k in REQUIRED_COMPONENT_KEYS)
    confidence = 0.75 if complete else 0.4
    return components, complete, confidence, parser_name


def parse_address(raw_address: str, country_hint: str | None) -> tuple[dict[str, str | None], bool, float]:
    """Return (parsed_components, is_complete, confidence_score)."""
    components, complete, confidence, _ = parse_address_with_provider(raw_address, country_hint)
    return components, complete, confidence


def _parse_with_provider(raw_address: str, country_hint: str | None) -> tuple[dict[str, str | None], str]:
    if _should_use_heuristic_first(raw_address):
        return _heuristic_parse(raw_address, country_hint), "heuristic"

    parsed = _parse_with_usaddress(raw_address, country_hint)
    if parsed is not None:
        return parsed, "usaddress"
    return _heuristic_parse(raw_address, country_hint), "heuristic"


def _should_use_heuristic_first(raw_address: str) -> bool:
    """Preserve legacy handling for sparse or malformed comma-fragment inputs."""
    parts = [segment.strip() for segment in raw_address.split(",") if segment.strip()]
    return len(parts) <= 1


def _parse_with_usaddress(raw_address: str, country_hint: str | None) -> dict[str, str | None] | None:
    """Parse using local usaddress when installed; return None when unavailable/unparsable."""
    _ = country_hint
    try:
        import usaddress  # type: ignore[import-untyped]
    except ImportError:
        return None

    try:
        tagged, _ = usaddress.tag(raw_address)
    except Exception:
        return None

    street_parts = [
        tagged.get("AddressNumber"),
        tagged.get("StreetNamePreDirectional"),
        tagged.get("StreetNamePreType"),
        tagged.get("StreetName"),
        tagged.get("StreetNamePostType"),
        tagged.get("StreetNamePostDirectional"),
    ]
    street_line = " ".join(part.strip() for part in street_parts if part and part.strip()) or None

    city = tagged.get("PlaceName")
    state = tagged.get("StateName")
    postal_code = tagged.get("ZipCode")
    country = country_hint or None

    return {
        "street_line": street_line,
        "city": city.strip() if isinstance(city, str) and city.strip() else None,
        "state": state.strip() if isinstance(state, str) and state.strip() else None,
        "postal_code": postal_code.strip() if isinstance(postal_code, str) and postal_code.strip() else None,
        "country": country,
    }


def _heuristic_parse(raw_address: str, country_hint: str | None) -> dict[str, str | None]:
    """Fallback parser that preserves existing behavior when no local parser is installed."""
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
