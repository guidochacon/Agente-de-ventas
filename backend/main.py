import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from config import settings
from models.database import init_db
from api.chat import router as chat_router
from api.coach import router as coach_router
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
app.include_router(coach_router)
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


@app.get("/coach", response_class=HTMLResponse)
async def coach_page():
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coach IA — Scaling In Blue</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; height: 100dvh; display: flex; flex-direction: column; }

    header { padding: 16px 24px; border-bottom: 1px solid #1e293b; display: flex; align-items: center; gap: 12px; }
    header h1 { font-size: 18px; font-weight: 600; color: #f1f5f9; }
    header span { font-size: 12px; color: #64748b; }

    .modes { display: flex; gap: 8px; padding: 16px 24px; border-bottom: 1px solid #1e293b; flex-wrap: wrap; }
    .mode-btn {
      padding: 8px 18px; border-radius: 20px; border: 1px solid #334155;
      background: transparent; color: #94a3b8; cursor: pointer; font-size: 14px;
      transition: all .15s;
    }
    .mode-btn:hover { border-color: #2563eb; color: #93c5fd; }
    .mode-btn.active { background: #2563eb; border-color: #2563eb; color: #fff; font-weight: 500; }

    .mode-hint { padding: 10px 24px; font-size: 13px; color: #64748b; background: #0f172a; border-bottom: 1px solid #1e293b; min-height: 40px; }

    .messages { flex: 1; overflow-y: auto; padding: 24px; display: flex; flex-direction: column; gap: 16px; }

    .msg { max-width: 76%; display: flex; flex-direction: column; gap: 4px; }
    .msg.user { align-self: flex-end; align-items: flex-end; }
    .msg.agent { align-self: flex-start; }

    .bubble {
      padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6;
      white-space: pre-wrap; word-break: break-word;
    }
    .msg.user .bubble { background: #2563eb; color: #fff; border-bottom-right-radius: 4px; }
    .msg.agent .bubble { background: #1e293b; color: #e2e8f0; border-bottom-left-radius: 4px; }

    .bubble strong { font-weight: 600; }
    .bubble em { font-style: italic; color: #93c5fd; }

    .typing { display: flex; gap: 4px; padding: 12px 16px; background: #1e293b; border-radius: 16px; border-bottom-left-radius: 4px; width: fit-content; }
    .typing span { width: 6px; height: 6px; background: #64748b; border-radius: 50%; animation: bounce .9s infinite; }
    .typing span:nth-child(2) { animation-delay: .15s; }
    .typing span:nth-child(3) { animation-delay: .3s; }
    @keyframes bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }

    .input-area { padding: 16px 24px; border-top: 1px solid #1e293b; display: flex; gap: 10px; align-items: flex-end; }
    textarea {
      flex: 1; background: #1e293b; border: 1px solid #334155; border-radius: 12px;
      padding: 12px 14px; color: #e2e8f0; font-size: 14px; resize: none;
      min-height: 44px; max-height: 160px; outline: none; font-family: inherit; line-height: 1.5;
    }
    textarea:focus { border-color: #2563eb; }
    textarea::placeholder { color: #475569; }
    button#send {
      background: #2563eb; border: none; color: #fff; border-radius: 10px;
      width: 44px; height: 44px; cursor: pointer; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: background .15s;
    }
    button#send:hover { background: #1d4ed8; }
    button#send:disabled { background: #334155; cursor: default; }
    button#send svg { width: 18px; height: 18px; }
  </style>
</head>
<body>

<header>
  <div>
    <h1>Coach IA · Scaling In Blue</h1>
    <span>Powered by tu knowledge base de llamadas reales</span>
  </div>
</header>

<div class="modes">
  <button class="mode-btn" data-mode="analyze">Analizar llamada</button>
  <button class="mode-btn active" data-mode="consult">Consultar técnica</button>
  <button class="mode-btn" data-mode="practice">Practicar cierre</button>
</div>
<div class="mode-hint" id="hint"></div>

<div class="messages" id="messages"></div>

<div class="input-area">
  <textarea id="input" placeholder="Escribí tu mensaje..." rows="1"></textarea>
  <button id="send">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
    </svg>
  </button>
</div>

<script>
const HINTS = {
  analyze: "Pegá una transcripción o describí una llamada → te digo qué funcionó, qué mejorar y qué técnica aplicar.",
  consult: "Preguntame cualquier cosa: «¿cómo manejo X objeción?», «el cliente me dijo Y, ¿qué hago?»",
  practice: "Practicá tu cierre. Yo juego de prospecto con dudas reales. Empezá la llamada cuando quieras.",
};

let ws = null;
let currentMode = "consult";
let sessionId = "coach-" + Math.random().toString(36).slice(2);
let responding = false;

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
const hintEl = document.getElementById("hint");

function setHint(mode) {
  hintEl.textContent = HINTS[mode] || "";
}

function connect(mode) {
  if (ws) { ws.onclose = null; ws.close(); }
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/api/coach/${sessionId}?mode=${mode}`);

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "start") {
      addAgentBubble("");
    } else if (msg.type === "token") {
      appendToLastBubble(msg.text);
    } else if (msg.type === "end") {
      setResponding(false);
    } else if (msg.type === "error") {
      appendToLastBubble("\\n[Error: " + msg.message + "]");
      setResponding(false);
    }
  };

  ws.onclose = () => {
    setTimeout(() => { if (currentMode === mode) connect(mode); }, 2000);
  };
}

function setMode(mode) {
  currentMode = mode;
  sessionId = "coach-" + Math.random().toString(36).slice(2);
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  setHint(mode);
  messagesEl.innerHTML = "";
  connect(mode);
}

function addUserBubble(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.innerHTML = `<div class="bubble">${escHtml(text)}</div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addAgentBubble(text) {
  const div = document.createElement("div");
  div.className = "msg agent";
  div.innerHTML = `<div class="bubble"></div>`;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return div.querySelector(".bubble");
}

function appendToLastBubble(text) {
  const bubbles = messagesEl.querySelectorAll(".msg.agent .bubble");
  const last = bubbles[bubbles.length - 1];
  if (last) {
    last.textContent += text;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
}

function escHtml(t) {
  return t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

function setResponding(val) {
  responding = val;
  sendBtn.disabled = val;
  inputEl.disabled = val;
}

function send() {
  const text = inputEl.value.trim();
  if (!text || responding) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) { alert("Conectando, esperá un momento..."); return; }

  addUserBubble(text);
  inputEl.value = "";
  inputEl.style.height = "auto";
  setResponding(true);

  ws.send(JSON.stringify({ message: text }));
}

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + "px";
});

document.querySelectorAll(".mode-btn").forEach(btn => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

// Init
setHint(currentMode);
connect(currentMode);
</script>
</body>
</html>"""


@app.get("/health")
async def health():
    return {"status": "ok", "agent": settings.agent_name}
