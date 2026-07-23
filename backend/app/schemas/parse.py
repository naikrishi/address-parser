from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ParseCreateRequest(BaseModel):
    raw_address: str = Field(min_length=1, max_length=500)
    input_source: str = Field(default="manual", min_length=1, max_length=100)
    country_hint: str | None = Field(default=None, max_length=100)

    @field_validator("raw_address")
    @classmethod
    def validate_raw_address(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("raw_address must not be blank")
        return trimmed

    @field_validator("input_source")
    @classmethod
    def validate_input_source(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("input_source must not be blank")
        return trimmed

    @field_validator("country_hint")
    @classmethod
    def normalize_country_hint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None


class RawInputSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_address: str
    input_source: str
    country_hint: str | None
    created_at: datetime


class EnrichmentResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parse_result_id: UUID
    provider_name: str
    status: str
    enriched_components: dict[str, str | None]
    is_complete: bool
    confidence_score: float | None
    error_message: str | None
    created_at: datetime


class GeocodeResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parse_result_id: UUID
    enrichment_result_id: UUID | None
    provider_name: str
    status: str
    latitude: float | None
    longitude: float | None
    result_payload: dict[str, str | float | int | bool | None]
    error_message: str | None
    created_at: datetime


class ParseResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_input_id: UUID
    parser_name: str
    parsed_components: dict[str, str | None]
    is_complete: bool
    confidence_score: float
    created_at: datetime
    raw_input: RawInputSummary
    enrichment_results: list[EnrichmentResultResponse] = Field(default_factory=list)
    geocode_results: list[GeocodeResultResponse] = Field(default_factory=list)


class ParseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_input_id: UUID
    parser_name: str
    is_complete: bool
    confidence_score: float
    created_at: datetime
    raw_address: str
    input_source: str
    country_hint: str | None
    enrichment_result_count: int
    geocode_result_count: int
    latest_enrichment_status: str | None
    latest_geocode_status: str | None


class InputListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    raw_address: str
    input_source: str
    country_hint: str | None
    created_at: datetime
    parse_result_count: int
    enrichment_result_count: int
    geocode_result_count: int
    has_enrichment: bool
    has_geocode: bool


class ParseListResponse(BaseModel):
    items: list[ParseListItem]
    total: int
    limit: int
    offset: int


class InputsListResponse(BaseModel):
    items: list[InputListItem]
    total: int
    limit: int
    offset: int
