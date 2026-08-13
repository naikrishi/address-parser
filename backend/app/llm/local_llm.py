"""Local LLM adapter for enrichment workflows.

Supports:
- Ollama (`/api/generate`)
- OpenAI-compatible local servers like LM Studio (`/v1/chat/completions`)
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


def is_local_llm_configured(base_url: str, model: str) -> bool:
    return bool(base_url and model)


@retry(
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError)),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
def call_local_llm(
    *,
    provider: str,
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout_seconds: int,
) -> tuple[dict[str, Any], int, int, str]:
    """Return (parsed_json, prompt_tokens, completion_tokens, provider_name)."""
    if provider == "ollama":
        return _call_ollama(base_url, model, prompt, timeout_seconds)
    return _call_openai_compatible(base_url, model, prompt, max_tokens, timeout_seconds)


def _call_ollama(
    base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: int,
) -> tuple[dict[str, Any], int, int, str]:
    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data.get("response", "{}")
        parsed = json.loads(content)
        return parsed, 0, 0, model


def _call_openai_compatible(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    timeout_seconds: int,
) -> tuple[dict[str, Any], int, int, str]:
    with httpx.Client(timeout=timeout_seconds) as client:
        resp = client.post(
            f"{base_url.rstrip('/')}/v1/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        parsed = json.loads(content)
        return parsed, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0), model
