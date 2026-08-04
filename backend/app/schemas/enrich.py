from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnrichRequest(BaseModel):
    parse_result_id: UUID


class EnrichmentStepTrace(BaseModel):
    step: int
    provider: str
    status: str  # complete | partial | skipped | error
    prompt_tokens: int = 0
    completion_tokens: int = 0
    estimated_cost: float = 0.0


class EnrichResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parse_result_id: UUID
    enrichment_result_id: UUID
    geocode_result_id: UUID | None
    enriched_components: dict[str, str | None]
    is_complete: bool
    confidence_label: str | None
    latitude: float | None
    longitude: float | None
    steps: list[EnrichmentStepTrace]
    total_estimated_cost: float
    created_at: datetime


class ParseSummaryResponse(BaseModel):
    parse_result_id: UUID
    summary: str
    confidence_label: str | None
    generated_at: datetime
