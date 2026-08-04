import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_database_url() -> str:
    """Return the database URL from environment with a safe local default."""
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://app:app@127.0.0.1:5432/address_parser",
    )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://app:app@127.0.0.1:5432/address_parser",
        alias="DATABASE_URL",
    )

    # Embeddings
    embeddings_provider: Literal["local", "company_api"] = Field(
        default="local", alias="EMBEDDINGS_PROVIDER"
    )
    embeddings_model: str = Field(
        default="all-MiniLM-L6-v2", alias="EMBEDDINGS_MODEL"
    )
    embeddings_dimension: int = Field(default=384, alias="EMBEDDINGS_DIMENSION")
    embeddings_api_base_url: str = Field(default="", alias="EMBEDDINGS_API_BASE_URL")
    embeddings_api_key: str = Field(default="", alias="EMBEDDINGS_API_KEY")
    embeddings_timeout_seconds: int = Field(default=30, alias="EMBEDDINGS_TIMEOUT_SECONDS")
    embeddings_fallback_enabled: bool = Field(default=True, alias="EMBEDDINGS_FALLBACK_ENABLED")

    # LLM (company proxy; placeholders until model IDs are approved)
    openai_api_base_url: str = Field(default="", alias="OPENAI_API_BASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    llm_gap_fill_model: str = Field(default="gpt-4o", alias="LLM_GAP_FILL_MODEL")
    llm_search_model: str = Field(default="gpt-4o-search-preview", alias="LLM_SEARCH_MODEL")
    llm_timeout_seconds: int = Field(default=60, alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")

    # Serper (placeholder until key is issued)
    serper_api_key: str = Field(default="", alias="SERPER_API_KEY")
    serper_api_base_url: str = Field(
        default="https://api.serper.dev", alias="SERPER_API_BASE_URL"
    )
    serper_timeout_seconds: int = Field(default=15, alias="SERPER_TIMEOUT_SECONDS")

    # Cost estimator — GPT-4o public list pricing (USD per 1k tokens as of 2025)
    cost_input_per_1k_tokens: float = Field(
        default=0.005, alias="COST_INPUT_PER_1K_TOKENS"
    )
    cost_output_per_1k_tokens: float = Field(
        default=0.015, alias="COST_OUTPUT_PER_1K_TOKENS"
    )

    # Proxy / CA bundle for corporate networks
    https_proxy: str = Field(default="", alias="HTTPS_PROXY")
    ssl_cert_file: str = Field(default="", alias="SSL_CERT_FILE")

    @field_validator("embeddings_dimension")
    @classmethod
    def validate_dimension(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("embeddings_dimension must be positive")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
