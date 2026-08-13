"""Steps 2 and 3 of the enrichment pipeline.

Step 2: GPT-4o gap fill — called when required fields are missing after Step 1.
Step 3: gpt-4o-search-preview web search — called when Step 2 still leaves gaps.

Both steps require OPENAI_API_KEY and OPENAI_API_BASE_URL to be set.
When not configured, stubs are returned so the pipeline can run locally.
"""

from __future__ import annotations

import json
import logging

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.llm.local_llm import call_local_llm, is_local_llm_configured
from app.services.cost import estimate_cost

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["street_line", "city", "state", "postal_code"]

_STEP2_PROMPT = """\
You are an address parser. Given the raw address and partial parse below, fill in
any missing or null fields and return ONLY a JSON object with these keys:
street_line, city, state, postal_code, country.

Use null for any field you cannot determine. Do not guess.

Raw address: {raw_address}
Partial parse: {partial}
"""

_STEP3_PROMPT = """\
Search the web to find the correct values for the missing address fields below.
Return ONLY a JSON object with keys: street_line, city, state, postal_code, country.
Use null for fields that cannot be confirmed.

Raw address: {raw_address}
Current parse (incomplete): {partial}
Missing fields: {missing}
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
def _call_chat(model: str, prompt: str) -> tuple[dict, int, int]:
    """Return (parsed_json, prompt_tokens, completion_tokens)."""
    settings = get_settings()

    if is_local_llm_configured(settings.llm_local_base_url, settings.llm_local_model):
        parsed, pt, ct, _ = call_local_llm(
            provider=settings.llm_local_provider,
            base_url=settings.llm_local_base_url,
            model=settings.llm_local_model,
            prompt=prompt,
            max_tokens=256,
            timeout_seconds=settings.llm_local_timeout_seconds,
        )
        return parsed, pt, ct

    if settings.use_local_models_only:
        raise RuntimeError("Local-only mode enabled but local LLM is not configured")

    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        resp = client.post(
            f"{settings.openai_api_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 256,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return json.loads(content), usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)


def _merge(base: dict, update: dict) -> dict:
    """Fill null/missing keys in base from update; never overwrite existing values."""
    return {k: base.get(k) or update.get(k) for k in set(base) | set(update)}


def _missing(components: dict) -> list[str]:
    return [f for f in REQUIRED_FIELDS if not components.get(f)]


def run_step2(
    raw_address: str, components: dict
) -> tuple[dict, int, int, float, str]:
    """GPT-4o gap fill. Returns (merged_components, prompt_tokens, completion_tokens, cost_usd, provider)."""
    if not _missing(components):
        return components, 0, 0, 0.0, "skipped"

    if not _llm_available():
        logger.warning("Step 2 skipped: LLM not configured")
        return components, 0, 0, 0.0, "stub"

    settings = get_settings()
    prompt = _STEP2_PROMPT.format(raw_address=raw_address, partial=json.dumps(components))
    try:
        filled, pt, ct = _call_chat(settings.llm_gap_fill_model, prompt)
        merged = _merge(components, filled)
        using_local = is_local_llm_configured(settings.llm_local_base_url, settings.llm_local_model)
        provider_name = settings.llm_local_model if using_local else settings.llm_gap_fill_model
        cost = 0.0 if using_local else estimate_cost(pt, ct)
        return merged, pt, ct, cost, provider_name
    except Exception as exc:
        logger.error("Step 2 LLM call failed: %s", exc)
        return components, 0, 0, 0.0, "error"


def run_step3(
    raw_address: str, components: dict
) -> tuple[dict, int, int, float, str]:
    """gpt-4o-search-preview web search. Returns (merged, prompt_tokens, completion_tokens, cost_usd, provider)."""
    missing = _missing(components)
    if not missing:
        return components, 0, 0, 0.0, "skipped"

    if not _llm_available():
        logger.warning("Step 3 skipped: LLM not configured")
        return components, 0, 0, 0.0, "stub"

    settings = get_settings()
    prompt = _STEP3_PROMPT.format(
        raw_address=raw_address, partial=json.dumps(components), missing=", ".join(missing)
    )
    try:
        filled, pt, ct = _call_chat(settings.llm_search_model, prompt)
        merged = _merge(components, filled)
        using_local = is_local_llm_configured(settings.llm_local_base_url, settings.llm_local_model)
        provider_name = settings.llm_local_model if using_local else settings.llm_search_model
        cost = 0.0 if using_local else estimate_cost(pt, ct)
        return merged, pt, ct, cost, provider_name
    except Exception as exc:
        logger.error("Step 3 LLM search call failed: %s", exc)
        return components, 0, 0, 0.0, "error"
