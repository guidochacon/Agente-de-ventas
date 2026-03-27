import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from config import settings
from models.database import init_db
from api.chat import router as chat_router
from api.leads import router as leads_router
from api.knowledge import router as knowledge_router
from api.quotes import router as quotes_router
from api.scheduling import router as scheduling_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Agente de Ventas",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(chat_router)
app.include_router(leads_router)
app.include_router(knowledge_router)
app.include_router(quotes_router)
app.include_router(scheduling_router)

# Serve widget
WIDGET_DIST = os.path.join(os.path.dirname(__file__), "..", "widget", "dist")
if os.path.exists(WIDGET_DIST):
    app.mount("/widget", StaticFiles(directory=WIDGET_DIST), name="widget")

# Serve admin
ADMIN_DIR = os.path.join(os.path.dirname(__file__), "..", "admin")
if os.path.exists(ADMIN_DIR):
    app.mount("/admin-static", StaticFiles(directory=ADMIN_DIR), name="admin-static")


@app.get("/", response_class=HTMLResponse)
async def demo_page():
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agente de Ventas — Demo</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 80px auto; padding: 24px; color: #333; }
    h1 { color: #2563EB; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
    .links a { display: inline-block; margin-right: 16px; color: #2563EB; }
  </style>
</head>
<body>
  <h1>🤖 Agente de Ventas</h1>
  <p>El backend está corriendo correctamente.</p>
  <h3>Links útiles</h3>
  <div class="links">
    <a href="/docs">API Docs</a>
    <a href="/admin">Admin</a>
    <a href="/api/leads">Leads</a>
    <a href="/api/knowledge">Base de Conocimiento</a>
  </div>
  <h3>Widget embed</h3>
  <pre><code>&lt;script&gt;
  window.SalesAgentConfig = {
    agentUrl: "http://localhost:8000",
    agentName: "Alex",
    primaryColor: "#2563EB"
  };
&lt;/script&gt;
&lt;script src="http://localhost:8000/widget/sales-agent-widget.min.js" async&gt;&lt;/script&gt;</code></pre>

  <!-- Load widget for demo -->
  <script>
    window.SalesAgentConfig = {
      agentUrl: window.location.origin,
      agentName: "Alex",
      primaryColor: "#2563EB",
      welcomeMessage: "¡Hola! Soy Alex, ¿en qué puedo ayudarte hoy?",
    };
  </script>
  <script src="/widget/sales-agent-widget.min.js" async></script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
async def admin_page():
    with open(os.path.join(ADMIN_DIR, "index.html")) as f:
        return f.read()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": settings.agent_name}
