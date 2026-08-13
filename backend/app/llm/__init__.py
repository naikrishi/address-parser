"""LLM integration package for enrichment and local provider adapters."""

from .local_llm import call_local_llm, is_local_llm_configured

__all__ = ["call_local_llm", "is_local_llm_configured"]
