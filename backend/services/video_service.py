"""
Instagram Reels video generator and editor with motion graphics.
Produces 1080x1920 MP4 files using Pillow (frames) + MoviePy (encoding).
Video editor adds auto-subtitles (faster-whisper) and motion graphics overlays.
"""
import os
import re
import uuid
import asyncio
import textwrap
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

REEL_WIDTH  = 1080
REEL_HEIGHT = 1920
FPS         = 30
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "..", "output", "videos")
KB_DIR      = os.path.join(os.path.dirname(__file__), "..", "knowledge_base")

BRAND = {
    "bg_dark":     (15,  23,  42),
    "bg_card":     (30,  41,  59),
    "accent":      (37,  99, 235),
    "accent_light":(147, 197, 253),
    "text_white":  (241, 245, 249),
    "text_muted":  (100, 116, 139),
    "text_dim":    (51,  65,  85),
    "success":     (34,  197,  94),
    "warning":     (251, 191,  36),
}

_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
]
_FONT_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
]

_executor = ThreadPoolExecutor(max_workers=2)


# ---------------------------------------------------------------------------
# Font helpers
# ---------------------------------------------------------------------------

def _load_font(candidates: list, size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


# ---------------------------------------------------------------------------
# Knowledge base extractor
# ---------------------------------------------------------------------------

class KnowledgeBaseExtractor:

    SKIP_PREFIXES = ("transcripcion_",)
    PRIORITY_FILES = [
        "errores_cierres_y_checklist.md",
        "mentalidad_y_tecnicas_cierre_avanzado.md",
        "guia_objeciones.md",
        "tipos_clientes_y_puntos_clave.md",
        "metricas_y_revision_llamadas.md",
        "objecion_lo_tengo_que_pensar.md",
        "objecion_confianza_framework.md",
        "seguimientos_framework.md",
        "sesgos_cognitivos_munger.md",
        "situaciones_especiales_llamada.md",
    ]

    @classmethod
    def extract_tips(cls, max_tips: int = 5) -> list[dict]:
        tips: list[dict] = []
        all_files = cls.PRIORITY_FILES + [
            f for f in os.listdir(KB_DIR)
            if f.endswith(".md") and f not in cls.PRIORITY_FILES
        ]
        for filename in all_files:
            if any(filename.startswith(p) for p in cls.SKIP_PREFIXES):
                continue
            filepath = os.path.join(KB_DIR, filename)
            if not os.path.exists(filepath):
                continue
            tips.extend(cls._parse_sections(filepath))
            if len(tips) >= max_tips:
                break
        return tips[:max_tips]

    @staticmethod
    def _parse_sections(filepath: str) -> list[dict]:
        sections = []
        try:
            with open(filepath, encoding="utf-8") as f:
                lines = f.readlines()
        except OSError:
            return []

        current_title = None
        current_body: list[str] = []

        def flush():
            if current_title:
                body = " ".join(current_body).strip()
                body = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", body)
                body = re.sub(r"`([^`]+)`", r"\1", body)
                body = body[:200].rsplit(" ", 1)[0] if len(body) > 200 else body
                if body:
                    sections.append({
                        "title": current_title.strip(),
                        "body": body,
                        "source": os.path.basename(filepath),
                    })

        for line in lines:
            if line.startswith("## ") or line.startswith("### "):
                flush()
                current_title = re.sub(r"^#+\s*", "", line).strip()
                current_body = []
            elif current_title and line.strip() and not line.startswith("#"):
                clean = line.strip()
                clean = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", clean)
                current_body.append(clean)
                if len(" ".join(current_body)) > 300:
                    pass  # let flush trim it

        flush()
        return sections


# ---------------------------------------------------------------------------
# Lead stats collector
# ---------------------------------------------------------------------------

class LeadStatsCollector:

    @staticmethod
    async def collect(db: AsyncSession) -> dict:
        from models.lead import Lead

        total_result = await db.execute(select(func.count()).select_from(Lead))
        total = total_result.scalar() or 0

        status_result = await db.execute(
            select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
        )
        by_status = {row[0]: row[1] for row in status_result.fetchall()}

        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_result = await db.execute(
            select(func.count()).select_from(Lead).where(Lead.created_at >= week_ago)
        )
        recent_week = recent_result.scalar() or 0

        closed = by_status.get("closed", 0) + by_status.get("won", 0)
        conversion_rate = round(closed / total * 100, 1) if total > 0 else 0.0

        return {
            "total_leads": total,
            "by_status": by_status,
            "recent_week": recent_week,
            "conversion_rate": conversion_rate,
        }


# ---------------------------------------------------------------------------
# Frame renderer
# ---------------------------------------------------------------------------

class FrameRenderer:

    def __init__(self):
        self.w = REEL_WIDTH
        self.h = REEL_HEIGHT

    # --- Backgrounds ---

    def make_base_frame(self) -> Image.Image:
        img = Image.new("RGB", (self.w, self.h), BRAND["bg_dark"])
        draw = ImageDraw.Draw(img)
        top = BRAND["bg_dark"]
        bot = (25, 35, 60)
        bands = 40
        band_h = self.h // bands
        for i in range(bands):
            t = i / bands
            r = int(top[0] + (bot[0] - top[0]) * t)
            g = int(top[1] + (bot[1] - top[1]) * t)
            b = int(top[2] + (bot[2] - top[2]) * t)
            draw.rectangle([(0, i * band_h), (self.w, (i + 1) * band_h)], fill=(r, g, b))
        return img

    def _draw_rounded_rect(self, draw: ImageDraw.Draw, xy, radius: int, fill):
        x0, y0, x1, y1 = xy
        draw.rectangle([(x0 + radius, y0), (x1 - radius, y1)], fill=fill)
        draw.rectangle([(x0, y0 + radius), (x1, y1 - radius)], fill=fill)
        draw.ellipse([(x0, y0), (x0 + radius * 2, y0 + radius * 2)], fill=fill)
        draw.ellipse([(x1 - radius * 2, y0), (x1, y0 + radius * 2)], fill=fill)
        draw.ellipse([(x0, y1 - radius * 2), (x0 + radius * 2, y1)], fill=fill)
        draw.ellipse([(x1 - radius * 2, y1 - radius * 2), (x1, y1)], fill=fill)

    def draw_text_wrapped(
        self,
        img: Image.Image,
        text: str,
        x: int,
        y: int,
        max_width: int,
        font: ImageFont.FreeTypeFont,
        color: tuple,
        align: str = "center",
    ) -> int:
        draw = ImageDraw.Draw(img)
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)

        line_h = font.getbbox("Ag")[3] - font.getbbox("Ag")[1] + 10
        cur_y = y
        for line in lines:
            bbox = font.getbbox(line)
            w = bbox[2] - bbox[0]
            if align == "center":
                lx = x + (max_width - w) // 2
            elif align == "right":
                lx = x + max_width - w
            else:
                lx = x
            draw.text((lx, cur_y), line, font=font, fill=color)
            cur_y += line_h
        return cur_y

    # --- Specific frames ---

    def make_title_frame(self, video_type: str, business_name: str) -> Image.Image:
        img = self.make_base_frame()
        draw = ImageDraw.Draw(img)

        label = "CONSEJOS DE VENTAS" if video_type == "tips" else "METRICAS DE VENTAS"
        font_big = _load_font(_FONT_CANDIDATES, 90)
        font_small = _load_font(_FONT_CANDIDATES, 36)
        font_label = _load_font(_FONT_REGULAR_CANDIDATES, 30)

        # Accent bar top
        self._draw_rounded_rect(draw, (440, 160, 640, 168), 4, BRAND["accent"])

        # Main label
        self.draw_text_wrapped(img, label, 80, 820, 920, font_big, BRAND["text_white"])

        # Business name
        self.draw_text_wrapped(img, business_name or "Tu Negocio", 80, 980, 920, font_small, BRAND["accent_light"])

        # Bottom tagline
        tagline = "Tips para cerrar mas ventas" if video_type == "tips" else "Resultados de tu equipo comercial"
        self.draw_text_wrapped(img, tagline, 80, 1100, 920, font_label, BRAND["text_muted"])

        # Decorative accent circle
        draw.ellipse([(820, 300), (1020, 500)], outline=BRAND["accent"], width=3)
        draw.ellipse([(50, 600), (150, 700)], fill=BRAND["bg_card"])

        return img

    def make_tip_frame(
        self,
        tip_number: int,
        total_tips: int,
        title: str,
        body: str,
        progress: float,
    ) -> Image.Image:
        img = self.make_base_frame()
        draw = ImageDraw.Draw(img)

        font_num = _load_font(_FONT_CANDIDATES, 180)
        font_label = _load_font(_FONT_CANDIDATES, 30)
        font_title = _load_font(_FONT_CANDIDATES, 54)
        font_body = _load_font(_FONT_REGULAR_CANDIDATES, 38)

        # "CONSEJO" label
        self.draw_text_wrapped(img, "CONSEJO DE VENTAS", 80, 200, 920, font_label, BRAND["accent"])

        # Big tip number
        num_str = f"{tip_number:02d}"
        bbox = font_num.getbbox(num_str)
        nx = (self.w - (bbox[2] - bbox[0])) // 2
        draw.text((nx, 280), num_str, font=font_num, fill=BRAND["text_white"])

        # Accent divider
        self._draw_rounded_rect(draw, (390, 520, 690, 530), 5, BRAND["accent"])

        # Title
        end_y = self.draw_text_wrapped(img, title, 80, 580, 920, font_title, BRAND["text_white"])

        # Body
        self.draw_text_wrapped(img, body, 80, end_y + 30, 920, font_body, BRAND["text_muted"])

        # Progress bar background
        bar_x, bar_y, bar_w, bar_h = 80, 1780, 920, 12
        self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 6, BRAND["bg_card"])
        fill_w = int(bar_w * progress)
        if fill_w > 12:
            self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), 6, BRAND["accent"])

        # Counter
        counter = f"{tip_number} / {total_tips}"
        font_counter = _load_font(_FONT_REGULAR_CANDIDATES, 28)
        self.draw_text_wrapped(img, counter, 80, 1810, 920, font_counter, BRAND["text_muted"])

        return img

    def make_metrics_frame(
        self,
        metric_name: str,
        value: str,
        subtitle: str,
        bar_pct: float,
        color: tuple,
    ) -> Image.Image:
        img = self.make_base_frame()
        draw = ImageDraw.Draw(img)

        font_label = _load_font(_FONT_CANDIDATES, 32)
        font_value = _load_font(_FONT_CANDIDATES, 180)
        font_sub = _load_font(_FONT_REGULAR_CANDIDATES, 42)

        # Card background
        self._draw_rounded_rect(draw, (60, 680, 1020, 1300), 24, BRAND["bg_card"])

        # Metric name label
        self.draw_text_wrapped(img, metric_name.upper(), 80, 200, 920, font_label, color)

        # Big value
        bbox = font_value.getbbox(value)
        vx = (self.w - (bbox[2] - bbox[0])) // 2
        draw.text((vx, 740), value, font=font_value, fill=BRAND["text_white"])

        # Subtitle
        self.draw_text_wrapped(img, subtitle, 80, 980, 920, font_sub, BRAND["text_muted"])

        # Animated bar
        bar_x, bar_y, bar_w, bar_h = 80, 1100, 920, 16
        self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), 8, BRAND["text_dim"])
        fill_w = max(16, int(bar_w * bar_pct))
        self._draw_rounded_rect(draw, (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), 8, color)

        # Bottom label
        font_hint = _load_font(_FONT_REGULAR_CANDIDATES, 28)
        self.draw_text_wrapped(img, "Agente de Ventas · metricas actualizadas", 80, 1820, 920, font_hint, BRAND["text_dim"])

        return img

    def make_outro_frame(self, cta_text: str, business_name: str) -> Image.Image:
        img = self.make_base_frame()
        draw = ImageDraw.Draw(img)

        font_big = _load_font(_FONT_CANDIDATES, 72)
        font_med = _load_font(_FONT_CANDIDATES, 44)
        font_small = _load_font(_FONT_REGULAR_CANDIDATES, 36)

        # Decorative elements
        self._draw_rounded_rect(draw, (0, 880, self.w, 1040), 0, BRAND["bg_card"])

        self.draw_text_wrapped(img, "Seguinos para", 80, 700, 920, font_med, BRAND["text_muted"])
        self.draw_text_wrapped(img, "mas contenido", 80, 780, 920, font_big, BRAND["text_white"])
        self.draw_text_wrapped(img, "de ventas", 80, 870, 920, font_big, BRAND["accent"])

        if cta_text:
            self.draw_text_wrapped(img, cta_text, 80, 1100, 920, font_med, BRAND["accent_light"])

        if business_name:
            self.draw_text_wrapped(img, business_name, 80, 1220, 920, font_small, BRAND["text_muted"])

        # Bottom accent bar
        self._draw_rounded_rect(draw, (440, 1750, 640, 1758), 4, BRAND["accent"])

        return img


# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------

def _arr(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))


def _build_fade_sequence(
    frame_a: Image.Image,
    frame_b: Image.Image,
    n: int,
) -> list[tuple[np.ndarray, int]]:
    a = _arr(frame_a).astype(np.float32)
    b = _arr(frame_b).astype(np.float32)
    frames = []
    for i in range(n):
        t = i / max(n - 1, 1)
        blended = np.clip(a * (1 - t) + b * t, 0, 255).astype(np.uint8)
        frames.append((blended, 1))
    return frames


def _build_slide_in_sequence(
    base: Image.Image,
    content: Image.Image,
    n: int,
    direction: str = "bottom",
) -> list[tuple[np.ndarray, int]]:
    base_arr = _arr(base)
    content_arr = _arr(content)
    h, w = base_arr.shape[:2]
    offset_max = 400
    frames = []
    for i in range(n):
        t = i / max(n - 1, 1)
        ease = 1 - (1 - t) ** 3
        offset = int(offset_max * (1 - ease))
        result = base_arr.copy()
        if direction == "bottom":
            src_start = max(0, offset)
            dst_start = max(0, -offset)
            rows = min(h - src_start, h - dst_start)
            if rows > 0:
                result[dst_start:dst_start + rows] = content_arr[src_start:src_start + rows]
        frames.append((result, 1))
    return frames


def _static_segment(img: Image.Image, n_frames: int) -> tuple[np.ndarray, int]:
    return (_arr(img), n_frames)


def _lookup_frame(segments: list[tuple[np.ndarray, int]], idx: int) -> np.ndarray:
    pos = 0
    for arr, count in segments:
        if idx < pos + count:
            return arr
        pos += count
    return segments[-1][0]


# ---------------------------------------------------------------------------
# VideoService
# ---------------------------------------------------------------------------

class VideoService:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(
        self,
        video_type: str,
        business_name: str = "",
        tips_count: int = 5,
        cta_text: str = "",
    ) -> dict:
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        data = await self._collect_data(video_type, tips_count)

        loop = asyncio.get_event_loop()
        segments = await loop.run_in_executor(
            _executor,
            self._build_segments,
            video_type, data, business_name, cta_text,
        )

        video_id = str(uuid.uuid4())
        filename = f"reel_{video_id}_{video_type}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)

        duration = await loop.run_in_executor(
            _executor,
            self._render_video,
            segments, output_path,
        )

        return {
            "video_id": video_id,
            "video_type": video_type,
            "file_path": output_path,
            "url": f"/api/videos/{video_id}",
            "duration_seconds": duration,
            "created_at": datetime.utcnow().isoformat(),
        }

    async def _collect_data(self, video_type: str, tips_count: int) -> dict:
        if video_type == "tips":
            return {"tips": KnowledgeBaseExtractor.extract_tips(tips_count)}
        else:
            stats = await LeadStatsCollector.collect(self.db)
            return {"stats": stats}

    def _build_segments(
        self,
        video_type: str,
        data: dict,
        business_name: str,
        cta_text: str,
    ) -> list[tuple[np.ndarray, int]]:
        renderer = FrameRenderer()
        if video_type == "tips":
            return self._build_tips_segments(renderer, data["tips"], business_name, cta_text)
        else:
            return self._build_metrics_segments(renderer, data["stats"], business_name, cta_text)

    def _build_tips_segments(
        self,
        renderer: FrameRenderer,
        tips: list[dict],
        business_name: str,
        cta_text: str,
    ) -> list[tuple[np.ndarray, int]]:
        segments: list[tuple[np.ndarray, int]] = []
        total = len(tips)

        title_img = renderer.make_title_frame("tips", business_name)
        segments.append(_static_segment(title_img, 45))  # 1.5s

        for i, tip in enumerate(tips):
            progress = (i + 1) / total
            tip_img = renderer.make_tip_frame(i + 1, total, tip["title"], tip["body"], progress)

            if i == 0:
                segments.extend(_build_fade_sequence(title_img, tip_img, 15))
            else:
                prev_progress = i / total
                prev_img = renderer.make_tip_frame(i, total, tips[i - 1]["title"], tips[i - 1]["body"], prev_progress)
                blank = renderer.make_base_frame()
                segments.extend(_build_slide_in_sequence(blank, tip_img, 15))

            segments.append(_static_segment(tip_img, 120))  # 4s hold

        outro_img = renderer.make_outro_frame(cta_text, business_name)
        blank = renderer.make_base_frame()
        segments.extend(_build_slide_in_sequence(blank, outro_img, 15))
        segments.append(_static_segment(outro_img, 60))  # 2s

        return segments

    def _build_metrics_segments(
        self,
        renderer: FrameRenderer,
        stats: dict,
        business_name: str,
        cta_text: str,
    ) -> list[tuple[np.ndarray, int]]:
        segments: list[tuple[np.ndarray, int]] = []

        title_img = renderer.make_title_frame("metrics", business_name)
        segments.append(_static_segment(title_img, 45))

        metrics = [
            {
                "name": "Leads totales",
                "value": str(stats["total_leads"]),
                "subtitle": "prospectos en el sistema",
                "target_pct": min(stats["total_leads"] / max(stats["total_leads"], 100), 1.0),
                "color": BRAND["accent"],
            },
            {
                "name": "Esta semana",
                "value": str(stats["recent_week"]),
                "subtitle": "nuevos leads en 7 dias",
                "target_pct": min(stats["recent_week"] / max(stats["total_leads"], 1), 1.0),
                "color": BRAND["success"],
            },
            {
                "name": "Conversion",
                "value": f"{stats['conversion_rate']:.0f}%",
                "subtitle": "leads cerrados / total",
                "target_pct": stats["conversion_rate"] / 100,
                "color": BRAND["warning"],
            },
        ]

        blank = renderer.make_base_frame()
        for metric in metrics:
            # animated bar: 30 frames going from 0 to target_pct
            for i in range(30):
                t = i / 29
                pct = metric["target_pct"] * (1 - (1 - t) ** 2)
                frame_img = renderer.make_metrics_frame(
                    metric["name"], metric["value"], metric["subtitle"], pct, metric["color"]
                )
                segments.append((_arr(frame_img), 1))

            final_frame = renderer.make_metrics_frame(
                metric["name"], metric["value"], metric["subtitle"],
                metric["target_pct"], metric["color"]
            )
            segments.append(_static_segment(final_frame, 90))  # 3s hold
            segments.extend(_build_slide_in_sequence(blank, blank, 15))  # slide-out

        outro_img = renderer.make_outro_frame(cta_text, business_name)
        segments.extend(_build_fade_sequence(blank, outro_img, 15))
        segments.append(_static_segment(outro_img, 60))

        return segments

    def _render_video(
        self,
        segments: list[tuple[np.ndarray, int]],
        output_path: str,
    ) -> float:
        from moviepy import VideoClip

        total_frames = sum(count for _, count in segments)
        total_seconds = total_frames / FPS

        def make_frame(t: float) -> np.ndarray:
            idx = min(int(t * FPS), total_frames - 1)
            return _lookup_frame(segments, idx)

        clip = VideoClip(make_frame, duration=total_seconds)
        clip.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio=False,
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
            logger=None,
        )
        clip.close()
        return total_seconds

    async def list_videos(self) -> list[dict]:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        videos = []
        with os.scandir(OUTPUT_DIR) as entries:
            for entry in sorted(entries, key=lambda e: e.stat().st_mtime, reverse=True):
                if not entry.name.endswith(".mp4"):
                    continue
                parts = entry.name.replace(".mp4", "").split("_")
                video_id = parts[1] if len(parts) > 1 else entry.name
                video_type = parts[2] if len(parts) > 2 else "unknown"
                stat = entry.stat()
                videos.append({
                    "video_id": video_id,
                    "video_type": video_type,
                    "filename": entry.name,
                    "url": f"/api/videos/{video_id}",
                    "size_bytes": stat.st_size,
                    "created_at": datetime.utcfromtimestamp(stat.st_mtime).isoformat(),
                })
        return videos

    async def get_video_path(self, video_id: str) -> str | None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        for entry in os.scandir(OUTPUT_DIR):
            if entry.name.endswith(".mp4") and video_id in entry.name:
                return entry.path
        return None


# ---------------------------------------------------------------------------
# Subtitle segment dataclass
# ---------------------------------------------------------------------------

class SubtitleSegment:
    __slots__ = ("start", "end", "text")

    def __init__(self, start: float, end: float, text: str):
        self.start = start
        self.end = end
        self.text = text.strip()


# ---------------------------------------------------------------------------
# VideoEditorService — edita un video existente con subtítulos y motion graphics
# ---------------------------------------------------------------------------

class VideoEditorService:
    """
    Takes an existing video file and adds:
    - Auto-generated subtitles via faster-whisper (local, no API key needed)
    - Optional animated intro (brand title card)
    - Optional lower-third with speaker name
    - Optional logo watermark in corner

    All rendering is CPU-bound; runs in a thread executor.
    """

    SUBTITLE_FONT_SIZE = 52
    SUBTITLE_MAX_CHARS = 42        # chars per line before wrapping
    SUBTITLE_PADDING_X = 30
    SUBTITLE_PADDING_Y = 20
    SUBTITLE_BOTTOM_OFFSET = 220   # px from bottom of frame
    SUBTITLE_BG_ALPHA = 180        # 0-255 transparency of pill background
    SUBTITLE_FADE_FRAMES = 6       # frames for fade-in/out

    def __init__(self):
        self._whisper_model = None  # lazy-load on first use

    def _get_whisper_model(self):
        if self._whisper_model is None:
            from faster_whisper import WhisperModel
            # "base" is ~150MB, fast, works offline; use "small" for better accuracy
            self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        return self._whisper_model

    async def edit(
        self,
        input_path: str,
        add_subtitles: bool = True,
        whisper_language: Optional[str] = None,   # None = auto-detect
        add_intro: bool = False,
        intro_title: str = "",
        intro_subtitle: str = "",
        lower_third_name: str = "",
        lower_third_duration: float = 4.0,
        business_name: str = "",
        cta_end: str = "",
    ) -> dict:
        """
        Main entry point. Returns same metadata dict as VideoService.generate().
        """
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        loop = asyncio.get_event_loop()

        # Step 1: Transcribe audio (blocking — run in executor)
        segments: list[SubtitleSegment] = []
        if add_subtitles:
            segments = await loop.run_in_executor(
                _executor,
                self._transcribe,
                input_path,
                whisper_language,
            )

        # Step 2: Render output video (blocking)
        video_id = str(uuid.uuid4())
        filename = f"reel_{video_id}_edited.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)

        duration = await loop.run_in_executor(
            _executor,
            self._render_edited,
            input_path,
            output_path,
            segments,
            add_intro,
            intro_title,
            intro_subtitle,
            lower_third_name,
            lower_third_duration,
            business_name,
            cta_end,
        )

        return {
            "video_id": video_id,
            "video_type": "edited",
            "file_path": output_path,
            "url": f"/api/videos/{video_id}",
            "duration_seconds": duration,
            "subtitle_segments": len(segments),
            "created_at": datetime.utcnow().isoformat(),
        }

    # --- Transcription ---

    def _transcribe(
        self,
        input_path: str,
        language: Optional[str],
    ) -> list[SubtitleSegment]:
        model = self._get_whisper_model()
        segs, _info = model.transcribe(
            input_path,
            language=language,
            beam_size=5,
            word_timestamps=False,
            vad_filter=True,               # skip silence automatically
        )
        result = []
        for seg in segs:
            text = seg.text.strip()
            if not text:
                continue
            # Split long segments into shorter lines for readability
            for chunk in self._split_segment(text, seg.start, seg.end):
                result.append(chunk)
        return result

    def _split_segment(
        self,
        text: str,
        start: float,
        end: float,
    ) -> list[SubtitleSegment]:
        """Break a long segment into ~6-word chunks with proportional timestamps."""
        words = text.split()
        max_words = 7
        if len(words) <= max_words:
            return [SubtitleSegment(start, end, text)]

        chunks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
        duration = end - start
        chunk_dur = duration / len(chunks)
        result = []
        for i, chunk in enumerate(chunks):
            cs = start + i * chunk_dur
            ce = cs + chunk_dur
            result.append(SubtitleSegment(cs, ce, " ".join(chunk)))
        return result

    # --- Video rendering ---

    def _render_edited(
        self,
        input_path: str,
        output_path: str,
        subtitle_segments: list[SubtitleSegment],
        add_intro: bool,
        intro_title: str,
        intro_subtitle: str,
        lower_third_name: str,
        lower_third_duration: float,
        business_name: str,
        cta_end: str,
    ) -> float:
        from moviepy import VideoFileClip, concatenate_videoclips, VideoClip, CompositeVideoClip

        source = VideoFileClip(input_path)
        src_w, src_h = source.size
        src_dur = source.duration

        clips = []
        time_offset = 0.0

        # --- Optional intro card (2.5s) ---
        intro_duration = 0.0
        if add_intro and (intro_title or business_name):
            intro_duration = 2.5
            renderer = FrameRenderer()
            title_img = renderer.make_title_frame(
                "tips",
                intro_title or business_name,
            )
            # Resize intro to match source video dimensions
            title_img_resized = title_img.resize((src_w, src_h), Image.LANCZOS)
            intro_arr = _arr(title_img_resized)

            def make_intro(t):
                return intro_arr

            intro_clip = VideoClip(make_intro, duration=intro_duration)
            intro_clip = intro_clip.with_fps(FPS)
            clips.append(intro_clip)
            time_offset = intro_duration

        # --- Main video with subtitle overlay ---
        subtitle_layer = self._make_subtitle_layer(
            subtitle_segments,
            src_w,
            src_h,
            src_dur,
        )

        # Lower-third overlay
        lower_third_layer = None
        if lower_third_name:
            lower_third_layer = self._make_lower_third(
                lower_third_name,
                src_w,
                src_h,
                lower_third_duration,
            )

        overlays = [source]
        if subtitle_layer:
            overlays.append(subtitle_layer)
        if lower_third_layer:
            overlays.append(lower_third_layer)

        main_clip = CompositeVideoClip(overlays)
        clips.append(main_clip)

        # --- Optional outro card (2s) ---
        if cta_end or business_name:
            renderer = FrameRenderer()
            outro_img = renderer.make_outro_frame(cta_end, business_name)
            outro_img_resized = outro_img.resize((src_w, src_h), Image.LANCZOS)
            outro_arr = _arr(outro_img_resized)
            outro_duration = 2.0

            def make_outro(t):
                return outro_arr

            outro_clip = VideoClip(make_outro, duration=outro_duration)
            outro_clip = outro_clip.with_fps(FPS)
            clips.append(outro_clip)

        # Concatenate and export
        final = concatenate_videoclips(clips) if len(clips) > 1 else clips[0]
        final.write_videofile(
            output_path,
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            ffmpeg_params=["-crf", "23", "-pix_fmt", "yuv420p"],
            logger=None,
        )

        total_duration = final.duration
        final.close()
        source.close()
        return total_duration

    # --- Subtitle overlay layer ---

    def _make_subtitle_layer(
        self,
        segments: list[SubtitleSegment],
        width: int,
        height: int,
        duration: float,
    ):
        if not segments:
            return None

        from moviepy import VideoClip

        font = _load_font(_FONT_CANDIDATES, self.SUBTITLE_FONT_SIZE)
        font_reg = _load_font(_FONT_REGULAR_CANDIDATES, self.SUBTITLE_FONT_SIZE)

        def make_frame(t: float) -> np.ndarray:
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            # Find active segment
            active = None
            for seg in segments:
                if seg.start <= t <= seg.end:
                    active = seg
                    break

            if active is None:
                return np.array(frame)

            # Fade alpha based on position within segment
            seg_dur = max(active.end - active.start, 0.1)
            elapsed = t - active.start
            fade_dur = self.SUBTITLE_FADE_FRAMES / FPS

            if elapsed < fade_dur:
                alpha = int(255 * (elapsed / fade_dur))
            elif elapsed > seg_dur - fade_dur:
                alpha = int(255 * ((seg_dur - elapsed) / fade_dur))
            else:
                alpha = 255

            alpha = max(0, min(255, alpha))

            # Wrap text
            lines = textwrap.wrap(active.text, width=self.SUBTITLE_MAX_CHARS)
            if not lines:
                return np.array(frame)

            # Measure total text block
            line_h = font.getbbox("Ag")[3] + 8
            total_text_h = len(lines) * line_h
            max_line_w = max(font.getbbox(ln)[2] for ln in lines)

            pill_w = max_line_w + self.SUBTITLE_PADDING_X * 2
            pill_h = total_text_h + self.SUBTITLE_PADDING_Y * 2
            pill_x = (width - pill_w) // 2
            pill_y = height - self.SUBTITLE_BOTTOM_OFFSET - pill_h

            # Draw pill background
            draw = ImageDraw.Draw(frame)
            bg_alpha = int(self.SUBTITLE_BG_ALPHA * alpha / 255)
            bg_color = (*BRAND["bg_dark"], bg_alpha)
            radius = 16

            def rr(d, xy, r, fill):
                x0, y0, x1, y1 = xy
                d.rectangle([(x0 + r, y0), (x1 - r, y1)], fill=fill)
                d.rectangle([(x0, y0 + r), (x1, y1 - r)], fill=fill)
                d.ellipse([(x0, y0), (x0 + r*2, y0 + r*2)], fill=fill)
                d.ellipse([(x1 - r*2, y0), (x1, y0 + r*2)], fill=fill)
                d.ellipse([(x0, y1 - r*2), (x0 + r*2, y1)], fill=fill)
                d.ellipse([(x1 - r*2, y1 - r*2), (x1, y1)], fill=fill)

            rr(draw, (pill_x, pill_y, pill_x + pill_w, pill_y + pill_h), radius, bg_color)

            # Draw text lines
            text_alpha = alpha
            text_color = (*BRAND["text_white"], text_alpha)
            cur_y = pill_y + self.SUBTITLE_PADDING_Y
            for line in lines:
                lw = font.getbbox(line)[2]
                lx = (width - lw) // 2
                draw.text((lx, cur_y), line, font=font, fill=text_color)
                cur_y += line_h

            return np.array(frame)

        clip = VideoClip(make_frame, duration=duration, is_mask=False)
        clip = clip.with_fps(FPS)
        return clip

    # --- Lower-third overlay ---

    def _make_lower_third(
        self,
        name: str,
        width: int,
        height: int,
        show_duration: float,
    ):
        from moviepy import VideoClip

        bar_h = 80
        bar_y = height - 220
        font_name = _load_font(_FONT_CANDIDATES, 38)
        font_role = _load_font(_FONT_REGULAR_CANDIDATES, 26)
        fade_dur = 0.4
        total_dur = show_duration + fade_dur * 2

        def make_frame(t: float) -> np.ndarray:
            frame = Image.new("RGBA", (width, height), (0, 0, 0, 0))

            if t < fade_dur:
                alpha = int(255 * (t / fade_dur))
            elif t > total_dur - fade_dur:
                alpha = int(255 * ((total_dur - t) / fade_dur))
            else:
                alpha = 255

            alpha = max(0, min(255, alpha))
            draw = ImageDraw.Draw(frame)

            # Accent bar
            bar_color = (*BRAND["accent"], alpha)
            draw.rectangle([(0, bar_y), (width, bar_y + 4)], fill=bar_color)

            # Name
            name_color = (*BRAND["text_white"], alpha)
            draw.text((40, bar_y + 12), name, font=font_name, fill=name_color)

            return np.array(frame)

        clip = VideoClip(make_frame, duration=total_dur, is_mask=False)
        clip = clip.with_fps(FPS)
        return clip
