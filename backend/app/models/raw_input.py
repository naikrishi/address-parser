from datetime import datetime
from uuid import uuid4
from uuid import UUID as UUIDType

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RawInput(Base):
    __tablename__ = "raw_input"

    id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    raw_address: Mapped[str] = mapped_column(Text, nullable=False)
    input_source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    country_hint: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    parse_results = relationship(
        "ParseResult",
        back_populates="raw_input",
        cascade="all, delete-orphan",
        order_by="ParseResult.created_at",
    )
