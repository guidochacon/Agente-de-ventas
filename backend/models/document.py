import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(300))
    source_type: Mapped[str] = mapped_column(String(20))  # pdf | url | text
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "chunk_count": self.chunk_count,
            "ingested_at": self.ingested_at.isoformat() if self.ingested_at else None,
        }
