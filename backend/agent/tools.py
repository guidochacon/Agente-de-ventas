"""
Claude tool schemas and dispatcher.
Each tool maps to a backend service action.
"""
from typing import Any

TOOLS = [
    {
        "name": "search_knowledge_base",
        "description": "Busca información en la base de conocimiento del negocio. Usá esta herramienta siempre que necesites responder preguntas sobre servicios, precios, procesos, casos de éxito, garantías, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "La consulta de búsqueda en lenguaje natural",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "capture_lead",
        "description": "Guarda los datos de contacto del prospecto. Usá esta herramienta cuando el prospecto haya compartido su nombre y/o email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Nombre del prospecto"},
                "email": {"type": "string", "description": "Email del prospecto"},
                "phone": {"type": "string", "description": "Teléfono del prospecto (opcional)"},
            },
            "required": ["name", "email"],
        },
    },
    {
        "name": "get_scheduling_link",
        "description": "Obtiene el link de Calendly para agendar una reunión o demo. Usá cuando el prospecto quiera coordinar una llamada.",
        "input_schema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Tipo de reunión: 'demo', 'consulta', 'seguimiento'",
                }
            },
            "required": ["event_type"],
        },
    },
    {
        "name": "generate_reel",
        "description": (
            "Genera un video de Instagram Reels con motion graphics. "
            "Usá 'tips' para crear un Reel con consejos de ventas de la base de conocimiento. "
            "Usá 'metrics' para crear un Reel con estadísticas de leads y conversiones. "
            "Usá esta herramienta cuando pidan crear contenido para redes sociales o Instagram."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "video_type": {
                    "type": "string",
                    "enum": ["tips", "metrics"],
                    "description": "Tipo: 'tips' para consejos de ventas, 'metrics' para estadísticas",
                },
                "tips_count": {
                    "type": "integer",
                    "description": "Cantidad de tips (solo tipo 'tips'). Default: 5, máximo: 7",
                    "default": 5,
                },
                "cta_text": {
                    "type": "string",
                    "description": "Texto de CTA para el final del video (opcional)",
                },
            },
            "required": ["video_type"],
        },
    },
    {
        "name": "generate_quote",
        "description": "Genera una cotización para el prospecto. Usá cuando el prospecto pida precios o una propuesta formal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_email": {"type": "string", "description": "Email del prospecto"},
                "service": {"type": "string", "description": "Nombre del servicio o programa"},
                "details": {"type": "string", "description": "Detalles relevantes de lo que necesita el prospecto"},
            },
            "required": ["service"],
        },
    },
]


async def execute_tool(
    tool_name: str,
    tool_input: dict,
    session_id: str,
    db=None,
) -> Any:
    """Dispatch tool call to the appropriate service."""
    from rag.retriever import retrieve
    from services.lead_service import LeadService
    from services.calendly_service import CalendlyService
    from services.quote_service import QuoteService

    if tool_name == "search_knowledge_base":
        query = tool_input.get("query", "")
        context = retrieve(query, n_results=5)
        if not context:
            return "No encontré información específica sobre eso en la base de conocimiento."
        return context

    elif tool_name == "capture_lead":
        if db is None:
            return "No se pudo guardar el lead (sin conexión a DB)."
        service = LeadService(db)
        lead = await service.upsert(
            name=tool_input.get("name"),
            email=tool_input.get("email"),
            phone=tool_input.get("phone"),
            session_id=session_id,
        )
        return f"Lead guardado correctamente. ID: {lead.id}"

    elif tool_name == "get_scheduling_link":
        event_type = tool_input.get("event_type", "consulta")
        service = CalendlyService()
        link = await service.get_scheduling_link(event_type)
        return link

    elif tool_name == "generate_quote":
        if db is None:
            return "No se pudo generar la cotización (sin conexión a DB)."
        service = QuoteService(db)
        quote = await service.create(
            lead_email=tool_input.get("lead_email"),
            service=tool_input.get("service", ""),
            details=tool_input.get("details", ""),
        )
        return f"Cotización generada. ID: {quote.id}. El prospecto puede descargarla en /api/quotes/{quote.id}/pdf"

    elif tool_name == "generate_reel":
        if db is None:
            return "No se pudo generar el video (sin conexión a DB)."
        from services.video_service import VideoService
        from config import settings
        service = VideoService(db)
        result = await service.generate(
            video_type=tool_input.get("video_type", "tips"),
            business_name=settings.agent_business_name,
            tips_count=tool_input.get("tips_count", 5),
            cta_text=tool_input.get("cta_text", ""),
        )
        duration = result.get("duration_seconds", 0)
        url = result.get("url", "")
        return (
            f"Reel de Instagram generado exitosamente. "
            f"Tipo: {result['video_type']}, Duración: {duration:.0f}s. "
            f"Descargalo en: {url}"
        )

    else:
        return f"Herramienta '{tool_name}' no reconocida."
