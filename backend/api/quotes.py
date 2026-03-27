import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from services.quote_service import QuoteService

router = APIRouter(prefix="/api/quotes")


@router.get("/{quote_id}")
async def get_quote(quote_id: str, db: AsyncSession = Depends(get_db)):
    service = QuoteService(db)
    quote = await service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote.to_dict()


@router.get("/{quote_id}/pdf")
async def download_quote_pdf(quote_id: str, db: AsyncSession = Depends(get_db)):
    service = QuoteService(db)
    quote = await service.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    if not quote.pdf_path or not os.path.exists(quote.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not generated yet")

    ext = os.path.splitext(quote.pdf_path)[1]
    media_type = "application/pdf" if ext == ".pdf" else "text/html"
    return FileResponse(
        quote.pdf_path,
        media_type=media_type,
        filename=f"cotizacion_{quote_id[:8]}{ext}",
    )
