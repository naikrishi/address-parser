from datetime import datetime
from uuid import uuid4
from uuid import UUID as UUIDType

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EnrichmentResult(Base):
    __tablename__ = "enrichment_result"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parse_result_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parse_result.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, default="stub")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    enriched_components: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_label: Mapped[str | None] = mapped_column(String(10), nullable=True)  # low/medium/high
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)  # USD
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    parse_result = relationship("ParseResult", back_populates="enrichment_results")
    geocode_results = relationship(
        "GeocodeResult",
        back_populates="enrichment_result",
        cascade="all, delete-orphan",
        order_by="GeocodeResult.created_at",
    )