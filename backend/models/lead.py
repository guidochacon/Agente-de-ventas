import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="new")
    source_page: Mapped[str | None] = mapped_column(String(500), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(200), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "source_page": self.source_page,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
