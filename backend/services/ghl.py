"""
GoHighLevel (GHL) CRM integration service.

Uses GHL API v2. Requires GHL_API_KEY and GHL_LOCATION_ID in env.
Docs: https://highlevel.stoplight.io/docs/integrations/
"""
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

GHL_BASE = "https://services.leadconnectorhq.com"


async def get_contacts(api_key: str, location_id: str, limit: int = 100) -> list[dict]:
    """Fetch contacts from GHL location."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Version": "2021-07-28",
        "Content-Type": "application/json",
    }
    params = {"locationId": location_id, "limit": limit}
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{GHL_BASE}/contacts/", headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("contacts", [])


async def sync_leads_from_ghl(db: AsyncSession, api_key: str, location_id: str) -> dict:
    """Pull GHL contacts and upsert into the Lead table."""
    from models.lead import Lead

    if not api_key or not location_id:
        return {"error": "GHL_API_KEY and GHL_LOCATION_ID must be configured"}

    contacts = await get_contacts(api_key, location_id)
    created = 0
    updated = 0

    for c in contacts:
        email = c.get("email") or ""
        if not email:
            continue

        result = await db.execute(select(Lead).where(Lead.email == email))
        existing = result.scalar_one_or_none()

        name = f"{c.get('firstName', '')} {c.get('lastName', '')}".strip() or c.get("name", "")
        phone = c.get("phone", "")
        source = c.get("source", "ghl")

        if existing:
            existing.name = name or existing.name
            existing.phone = phone or existing.phone
            updated += 1
        else:
            lead = Lead(
                name=name,
                email=email,
                phone=phone,
                source_page=source,
                utm_source="ghl",
                status="new",
            )
            db.add(lead)
            created += 1

    await db.commit()
    return {"synced": len(contacts), "created": created, "updated": updated}
