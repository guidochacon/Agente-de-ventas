import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    lead_id: Mapped[str | None] = mapped_column(String, ForeignKey("leads.id"), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String, ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))  # user | assistant | tool
    content: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
