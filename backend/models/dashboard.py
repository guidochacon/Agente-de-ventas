import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Float, Integer, Boolean, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base


class SalesAgent(Base):
    __tablename__ = "sales_agents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(50), default="agent")  # closer | setter | agent
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DailyEntry(Base):
    __tablename__ = "daily_entries"
    __table_args__ = (UniqueConstraint("agent_id", "date", name="uq_agent_date"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("sales_agents.id"), index=True)
    date: Mapped[str] = mapped_column(String(10), index=True)  # YYYY-MM-DD
    new_leads: Mapped[int] = mapped_column(Integer, default=0)
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    conversations: Mapped[int] = mapped_column(Integer, default=0)
    demos_booked: Mapped[int] = mapped_column(Integer, default=0)
    demos_showed: Mapped[int] = mapped_column(Integer, default=0)
    offers_made: Mapped[int] = mapped_column(Integer, default=0)
    closed_deals: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)
    cash_collected: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "date": self.date,
            "new_leads": self.new_leads,
            "total_calls": self.total_calls,
            "conversations": self.conversations,
            "demos_booked": self.demos_booked,
            "demos_showed": self.demos_showed,
            "offers_made": self.offers_made,
            "closed_deals": self.closed_deals,
            "revenue": self.revenue,
            "cash_collected": self.cash_collected,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EODReport(Base):
    __tablename__ = "eod_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String, ForeignKey("sales_agents.id"), index=True)
    date: Mapped[str] = mapped_column(String(10))  # YYYY-MM-DD
    role: Mapped[str] = mapped_column(String(50), default="agent")
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1-5
    focus_level: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 1-5
    health_level: Mapped[int | None] = mapped_column(Integer, nullable=True)   # 1-5
    tracker_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    post_call_forms: Mapped[bool] = mapped_column(Boolean, default=False)
    biggest_win: Mapped[str | None] = mapped_column(Text, nullable=True)
    biggest_challenge: Mapped[str | None] = mapped_column(Text, nullable=True)
    tomorrow_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "date": self.date,
            "role": self.role,
            "energy_level": self.energy_level,
            "focus_level": self.focus_level,
            "health_level": self.health_level,
            "tracker_completed": self.tracker_completed,
            "post_call_forms": self.post_call_forms,
            "biggest_win": self.biggest_win,
            "biggest_challenge": self.biggest_challenge,
            "tomorrow_plan": self.tomorrow_plan,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }
