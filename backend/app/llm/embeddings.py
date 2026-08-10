"""Embeddings provider: local sentence-transformers primary, company API when configured."""

from __future__ import annotations

import logging
import hashlib
import math
from typing import TYPE_CHECKING

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Lazy-loaded so startup is fast when only the local model is used
_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
        settings = get_settings()
        logger.info("Loading local embedding model: %s", settings.embeddings_model)
        _local_model = SentenceTransformer(settings.embeddings_model)
    return _local_model


def _embed_via_deterministic_fallback(text: str, dimension: int) -> list[float]:
    """Generate a stable embedding-like vector without external ML packages."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "big", signed=False)
    state = seed or 1
    values: list[float] = []
    for _ in range(dimension):
        state = (1664525 * state + 1013904223) % (2**32)
        values.append((state / 2**31) - 1.0)

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def serialize_for_embedding(raw_address: str, parsed_components: dict) -> str:
    """Deterministic text representation of an address for stable embeddings."""
    street = parsed_components.get("street_line") or ""
    city = parsed_components.get("city") or ""
    state = parsed_components.get("state") or ""
    postal = parsed_components.get("postal_code") or ""
    country = parsed_components.get("country") or ""
    # Stable field order; empty fields become empty strings so the structure never shifts
    return f"{raw_address} | {street} | {city} | {state} | {postal} | {country}".strip()


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _embed_via_company_api(text: str) -> list[float]:
    """Call company embedding API. Placeholder until endpoint/auth are confirmed."""
    settings = get_settings()
    # PLACEHOLDER: replace request body and response parsing once company API schema is confirmed
    proxies = {settings.https_proxy} if settings.https_proxy else None
    verify = settings.ssl_cert_file or True
    with httpx.Client(timeout=settings.embeddings_timeout_seconds, verify=verify) as client:
        resp = client.post(
            f"{settings.embeddings_api_base_url}/embeddings",
            headers={"Authorization": f"Bearer {settings.embeddings_api_key}"},
            json={"input": text, "model": settings.embeddings_model},
        )
        resp.raise_for_status()
        data = resp.json()
        # PLACEHOLDER: adjust key path to match company API response shape
        vector: list[float] = data["data"][0]["embedding"]
    return vector


def _embed_via_local_model(text: str) -> list[float]:
    settings = get_settings()
    try:
        model = _get_local_model()
    except ImportError:
        logger.info("sentence-transformers not installed; using deterministic fallback embeddings")
        return _embed_via_deterministic_fallback(text, settings.embeddings_dimension)

    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_text(raw_address: str, parsed_components: dict) -> list[float]:
    """Return a fixed-dimension embedding for the given address."""
    settings = get_settings()
    text = serialize_for_embedding(raw_address, parsed_components)

    if settings.embeddings_provider == "company_api" and settings.embeddings_api_base_url:
        try:
            vector = _embed_via_company_api(text)
        except Exception as exc:
            if settings.embeddings_fallback_enabled:
                logger.warning("Company API embedding failed (%s); falling back to local model", exc)
                vector = _embed_via_local_model(text)
            else:
                raise
    else:
        vector = _embed_via_local_model(text)

    if len(vector) != settings.embeddings_dimension:
        raise ValueError(
            f"Embedding dimension mismatch: expected {settings.embeddings_dimension}, got {len(vector)}"
        )
    return vector

