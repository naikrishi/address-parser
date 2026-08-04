from datetime import datetime
from uuid import uuid4
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class GeocodeResult(Base):
    __tablename__ = "geocode_result"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parse_result_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("parse_result.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrichment_result_id: Mapped[UUIDType | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("enrichment_result.id", ondelete="CASCADE"),
        nullable=True,
    )
    provider_name: Mapped[str] = mapped_column(String(100), nullable=False, default="stub")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    result_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)  # USD
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    parse_result = relationship("ParseResult", back_populates="geocode_results")
    enrichment_result = relationship("EnrichmentResult", back_populates="geocode_results")