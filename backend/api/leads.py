import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from models.database import get_db
from services.lead_service import LeadService

router = APIRouter(prefix="/api/leads")


class LeadUpdate(BaseModel):
    status: str | None = None
    notes: str | None = None


@router.get("")
async def list_leads(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    service = LeadService(db)
    leads = await service.list_leads(skip=skip, limit=limit)
    return {"leads": [l.to_dict() for l in leads], "total": len(leads)}


@router.get("/export")
async def export_leads(db: AsyncSession = Depends(get_db)):
    service = LeadService(db)
    leads = await service.list_leads(limit=10000)

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "name", "email", "phone", "status", "source_page", "notes", "created_at"],
    )
    writer.writeheader()
    for lead in leads:
        writer.writerow(lead.to_dict())

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads.csv"},
    )


@router.get("/{lead_id}")
async def get_lead(lead_id: str, db: AsyncSession = Depends(get_db)):
    service = LeadService(db)
    lead = await service.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead.to_dict()


@router.patch("/{lead_id}")
async def update_lead(lead_id: str, body: LeadUpdate, db: AsyncSession = Depends(get_db)):
    service = LeadService(db)
    lead = await service.update_status(lead_id, body.status or "new", body.notes)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead.to_dict()
