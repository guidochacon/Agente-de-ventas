"""
REST endpoints for Instagram Reels video generation and editing.
"""
import os
import shutil
import tempfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db

router = APIRouter(prefix="/api/videos", tags=["videos"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "output", "uploads")


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


@router.post("/edit")
async def edit_video(
    file: UploadFile = File(..., description="Video MP4 a editar"),
    add_subtitles: bool = Form(True, description="Generar subtitulos automaticos con IA"),
    language: str = Form("", description="Idioma del audio (es, en, auto). Default: auto-detect"),
    add_intro: bool = Form(False, description="Agregar tarjeta de intro animada"),
    intro_title: str = Form("", description="Titulo para la intro"),
    lower_third_name: str = Form("", description="Nombre para el lower-third (aparece 4s al inicio)"),
    cta_end: str = Form("", description="Texto de llamada a la accion al final"),
    db: AsyncSession = Depends(get_db),
):
    """
    Sube un video MP4 crudo y devuelve un MP4 editado con:
    - Subtitulos generados automaticamente (faster-whisper, corre local)
    - Intro animada opcional con colores de marca
    - Lower-third con nombre del speaker
    - Tarjeta final con CTA
    """
    if not file.filename or not file.filename.lower().endswith((".mp4", ".mov", ".avi", ".mkv")):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos de video (mp4, mov, avi, mkv)")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save uploaded file to temp path
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(dir=UPLOAD_DIR, suffix=suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        input_path = tmp.name

    try:
        from services.video_service import VideoEditorService
        from config import settings

        editor = VideoEditorService()
        result = await editor.edit(
            input_path=input_path,
            add_subtitles=add_subtitles,
            whisper_language=language if language and language != "auto" else None,
            add_intro=add_intro,
            intro_title=intro_title,
            intro_subtitle="",
            lower_third_name=lower_third_name,
            lower_third_duration=4.0,
            business_name=settings.agent_business_name,
            cta_end=cta_end,
        )
    finally:
        # Clean up upload temp file
        try:
            os.unlink(input_path)
        except OSError:
            pass

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
