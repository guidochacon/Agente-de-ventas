from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.lead import Lead
from models.conversation import Conversation


class LeadService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(
        self,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        session_id: str | None = None,
    ) -> Lead:
        """Create or update a lead. Uses email as dedup key."""
        existing = None
        if email:
            result = await self.db.execute(select(Lead).where(Lead.email == email))
            existing = result.scalar_one_or_none()

        if existing:
            if name:
                existing.name = name
            if phone:
                existing.phone = phone
            await self.db.commit()
            await self.db.refresh(existing)
            return existing

        # Link to conversation if possible
        source_page = None
        if session_id:
            result = await self.db.execute(
                select(Conversation).where(Conversation.session_id == session_id)
            )
            conv = result.scalar_one_or_none()
            if conv:
                source_page = conv.id

        lead = Lead(name=name, email=email, phone=phone, source_page=source_page)
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)
        return lead

    async def list_leads(self, skip: int = 0, limit: int = 100) -> list[Lead]:
        result = await self.db.execute(
            select(Lead).order_by(Lead.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_lead(self, lead_id: str) -> Lead | None:
        result = await self.db.execute(select(Lead).where(Lead.id == lead_id))
        return result.scalar_one_or_none()

    async def update_status(self, lead_id: str, status: str, notes: str | None = None) -> Lead | None:
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        lead.status = status
        if notes:
            lead.notes = notes
        await self.db.commit()
        await self.db.refresh(lead)
        return lead
