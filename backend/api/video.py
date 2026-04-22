"""
REST endpoints for Instagram Reels video generation.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db

router = APIRouter(prefix="/api/videos", tags=["videos"])


class GenerateVideoRequest(BaseModel):
    video_type: str = "tips"   # "tips" | "metrics"
    tips_count: int = 5
    cta_text: str = ""


@router.post("/generate")
async def generate_video(
    body: GenerateVideoRequest,
    db: AsyncSession = Depends(get_db),
):
    if body.video_type not in ("tips", "metrics"):
        raise HTTPException(status_code=400, detail="video_type debe ser 'tips' o 'metrics'")

    from services.video_service import VideoService
    from config import settings

    service = VideoService(db)
    result = await service.generate(
        video_type=body.video_type,
        business_name=settings.agent_business_name,
        tips_count=min(body.tips_count, 7),
        cta_text=body.cta_text,
    )
    return result


@router.get("")
async def list_videos(db: AsyncSession = Depends(get_db)):
    from services.video_service import VideoService
    service = VideoService(db)
    videos = await service.list_videos()
    return {"videos": videos, "total": len(videos)}


@router.get("/{video_id}")
async def download_video(video_id: str, db: AsyncSession = Depends(get_db)):
    from services.video_service import VideoService
    service = VideoService(db)
    path = await service.get_video_path(video_id)
    if not path:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"reel_{video_id[:8]}.mp4",
    )
