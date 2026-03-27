from fastapi import APIRouter, Request
from services.calendly_service import CalendlyService

router = APIRouter(prefix="/api/scheduling")


@router.get("/link")
async def get_link(event_type: str = "consulta"):
    service = CalendlyService()
    link = await service.get_scheduling_link(event_type)
    return {"link": link, "event_type": event_type}


@router.post("/webhook")
async def calendly_webhook(request: Request):
    """Receive Calendly event notifications."""
    payload = await request.json()
    event = payload.get("event", "")
    # TODO: Update lead status when appointment is confirmed
    print(f"[CALENDLY WEBHOOK] Event: {event}")
    return {"status": "ok"}
