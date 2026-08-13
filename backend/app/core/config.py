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
    model_config = SettingsConfigDict(
        # Look in the backend dir first, then the repo root (for local dev where CWD is backend/).
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime environment
    app_env: Literal["development", "production"] = Field(default="development", alias="APP_ENV")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://app:app@127.0.0.1:5432/address_parser",
        alias="DATABASE_URL",
    )

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"],
        alias="CORS_ORIGINS",
    )
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "OPTIONS"],
        alias="CORS_ALLOW_METHODS",
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["Authorization", "Content-Type", "Accept"],
        alias="CORS_ALLOW_HEADERS",
    )

    # Auth
    jwt_secret_key: str = Field(default="dev-only-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="REFRESH_TOKEN_EXPIRE_DAYS")
    auth_bcrypt_rounds: int = Field(default=12, alias="AUTH_BCRYPT_ROUNDS")
    auth_rate_limit_per_minute: int = Field(default=10, alias="AUTH_RATE_LIMIT_PER_MINUTE")
    auth_rate_limit_window_seconds: int = Field(default=60, alias="AUTH_RATE_LIMIT_WINDOW_SECONDS")

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

    # Local LLM provider settings (used by upcoming local-first enrichment path)
    llm_local_provider: Literal["ollama", "lm_studio"] = Field(
        default="ollama", alias="LLM_LOCAL_PROVIDER"
    )
    llm_local_base_url: str = Field(default="", alias="LLM_LOCAL_BASE_URL")
    llm_local_model: str = Field(default="", alias="LLM_LOCAL_MODEL")
    llm_local_timeout_seconds: int = Field(default=60, alias="LLM_LOCAL_TIMEOUT_SECONDS")

    # Local geocoder settings (used by upcoming local-first geocode path)
    geocoder_provider: Literal["nominatim", "none"] = Field(
        default="none", alias="GEOCODER_PROVIDER"
    )
    geocoder_base_url: str = Field(default="", alias="GEOCODER_BASE_URL")
    geocoder_timeout_seconds: int = Field(default=15, alias="GEOCODER_TIMEOUT_SECONDS")

    # If true, upcoming provider dispatch will skip remote providers and use local-only paths.
    use_local_models_only: bool = Field(default=False, alias="USE_LOCAL_MODELS_ONLY")

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

    @field_validator(
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "auth_bcrypt_rounds",
        "auth_rate_limit_per_minute",
        "auth_rate_limit_window_seconds",
        "llm_local_timeout_seconds",
        "geocoder_timeout_seconds",
    )
    @classmethod
    def validate_positive_ints(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("auth configuration values must be positive")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            parsed = [origin.strip() for origin in value.split(",") if origin.strip()]
            return parsed or ["http://localhost:5173", "http://127.0.0.1:5173"]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @field_validator("cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def parse_csv_to_list(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
