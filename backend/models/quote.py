import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id: Mapped[str | None] = mapped_column(String, ForeignKey("leads.id"), nullable=True)
    service: Mapped[str] = mapped_column(String(300))
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft | sent | accepted | rejected
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "lead_id": self.lead_id,
            "service": self.service,
            "details": self.details,
            "total_value": self.total_value,
            "currency": self.currency,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
