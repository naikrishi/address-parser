from datetime import datetime
from uuid import uuid4
from uuid import UUID as UUIDType

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ParseResult(Base):
    __tablename__ = "parse_result"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_input_id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("raw_input.id", ondelete="CASCADE"),
        nullable=False,
    )
    parser_name: Mapped[str] = mapped_column(String(100), nullable=False, default="libpostal")
    parsed_components: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    raw_input = relationship("RawInput", back_populates="parse_results")
