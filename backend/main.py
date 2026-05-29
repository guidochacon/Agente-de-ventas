import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

from config import settings
from models.database import init_db
from models import SalesAgent, AsyncSessionLocal
from api.chat import router as chat_router
from api.coach import router as coach_router
from api.leads import router as leads_router
from api.knowledge import router as knowledge_router
from api.quotes import router as quotes_router
from api.scheduling import router as scheduling_router
from api.dashboard import router as dashboard_router
from sqlalchemy import select


async def _seed_agents():
    import json as _json
    raw = settings.seed_agents
    if not raw:
        return
    try:
        agents_data = _json.loads(raw)
    except Exception:
        return
    async with AsyncSessionLocal() as db:
        for a in agents_data:
            result = await db.execute(select(SalesAgent).where(SalesAgent.email == a.get("email", "")))
            if not result.scalar_one_or_none():
                import uuid as _uuid
                db.add(SalesAgent(
                    id=str(_uuid.uuid4()),
                    name=a.get("name", "Agente"),
                    email=a.get("email", ""),
                    role=a.get("role", "agent"),
                ))
        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ChromaDB data is pre-built into the Docker image at build time.
    # Only need to create SQLite tables here (fast, non-blocking).
    await init_db()
    await _seed_agents()
    yield


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
app.include_router(dashboard_router)

# Serve dashboard
DASHBOARD_DIST = os.path.join(os.path.dirname(__file__), "..", "dashboard", "dist")
if os.path.exists(DASHBOARD_DIST):
    app.mount("/dashboard", StaticFiles(directory=DASHBOARD_DIST, html=True), name="dashboard")

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
async def coach_page(pw: str = ""):
    if settings.coach_password and pw != settings.coach_password:
        return HTMLResponse("""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>Coach IA</title>
<style>
  body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;height:100dvh;margin:0}
  .box{background:#1e293b;padding:40px;border-radius:16px;text-align:center;width:320px}
  h2{margin-bottom:8px;color:#f1f5f9}p{color:#64748b;font-size:14px;margin-bottom:24px}
  input{width:100%;padding:10px 14px;background:#0f172a;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:15px;margin-bottom:12px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#2563eb;border:none;border-radius:8px;color:#fff;font-size:15px;cursor:pointer;font-weight:500}
  button:hover{background:#1d4ed8}
</style></head>
<body><div class="box">
  <h2>Coach IA</h2><p>Guido Chacón · Acceso exclusivo para alumnos</p>
  <input type="password" id="pw" placeholder="Contraseña" onkeydown="if(event.key==='Enter')go()">
  <button onclick="go()">Entrar</button>
</div>
<script>function go(){const p=document.getElementById('pw').value;if(p)location.href='/coach?pw='+encodeURIComponent(p);}</script>
</body></html>""", status_code=401)
    coach_password_js = f'"{settings.coach_password}"' if settings.coach_password else '""'
    coach_daily_limit_js = str(settings.coach_daily_limit)
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Coach IA — Guido Chacón</title>
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

    .btn-clear {
      background: transparent; border: 1px solid #334155; color: #64748b;
      border-radius: 8px; padding: 4px 12px; font-size: 12px; cursor: pointer;
      transition: all .15s; white-space: nowrap;
    }
    .btn-clear:hover { border-color: #ef4444; color: #f87171; }
    .history-divider {
      text-align: center; font-size: 11px; color: #334155; margin: 4px 0;
      display: flex; align-items: center; gap: 8px;
    }
    .history-divider::before, .history-divider::after {
      content: ""; flex: 1; height: 1px; background: #1e293b;
    }
  </style>
</head>
<body>

<header>
  <div>
    <h1>Coach IA · Guido Chacón</h1>
    <span>Powered by tu knowledge base de llamadas reales</span>
  </div>
</header>

<div class="modes">
  <button class="mode-btn" data-mode="analyze">Analizar llamada</button>
  <button class="mode-btn active" data-mode="consult">Consultar técnica</button>
  <button class="mode-btn" data-mode="practice">Practicar cierre</button>
</div>
<div class="mode-hint" id="hint" style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
  <span id="hint-text"></span>
  <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
    <span id="msg-counter" style="font-size:11px;color:#475569;display:none"></span>
    <button class="btn-clear" id="btn-clear" style="display:none">Limpiar historial</button>
  </div>
</div>

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

const COACH_PW = """ + coach_password_js + """;
const DAILY_LIMIT = """ + coach_daily_limit_js + """;

// --- localStorage helpers ---
function storageKey(mode) { return "coach_history_" + mode; }
function sidKey(mode)     { return "coach_sid_" + mode; }

function loadHistory(mode) {
  try {
    const raw = localStorage.getItem(storageKey(mode));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    localStorage.removeItem(storageKey(mode));
    return [];
  }
}

function saveHistory(mode, history) {
  try {
    localStorage.setItem(storageKey(mode), JSON.stringify(history));
  } catch (e) {
    if (e.name === "QuotaExceededError" || e.code === 22) {
      const trimmed = history.slice(-30);
      try { localStorage.setItem(storageKey(mode), JSON.stringify(trimmed)); } catch (_) {}
    }
  }
}

function getOrCreateSid(mode) {
  let sid = localStorage.getItem(sidKey(mode));
  if (!sid) {
    sid = "coach-" + Math.random().toString(36).slice(2);
    localStorage.setItem(sidKey(mode), sid);
  }
  return sid;
}

let ws = null;
let currentMode = "consult";
let sessionId = getOrCreateSid(currentMode);
let responding = false;
let _history = loadHistory(currentMode);
let _agentBuf = "";

const messagesEl  = document.getElementById("messages");
const inputEl     = document.getElementById("input");
const sendBtn     = document.getElementById("send");
const hintTextEl  = document.getElementById("hint-text");
const clearBtn    = document.getElementById("btn-clear");
const counterEl   = document.getElementById("msg-counter");

function todayKey() { return "coach_used_" + new Date().toISOString().slice(0,10); }
function getDailyUsed() { return parseInt(localStorage.getItem(todayKey()) || "0"); }
function incrementDailyUsed() { localStorage.setItem(todayKey(), getDailyUsed() + 1); }

function updateCounter() {
  if (DAILY_LIMIT <= 0) return;
  const used = getDailyUsed();
  const left = Math.max(0, DAILY_LIMIT - used);
  counterEl.textContent = left + " mensajes hoy";
  counterEl.style.display = "inline";
  counterEl.style.color = left <= 5 ? "#f87171" : "#475569";
  sendBtn.disabled = left === 0 || responding;
  inputEl.disabled = left === 0;
  if (left === 0) inputEl.placeholder = "Límite diario alcanzado. Volvé mañana.";
}

function setHint(mode) {
  hintTextEl.textContent = HINTS[mode] || "";
}

function updateClearBtn() {
  clearBtn.style.display = _history.length > 0 ? "inline-block" : "none";
}

function renderHistory(history) {
  messagesEl.innerHTML = "";
  if (history.length === 0) return;
  const divider = document.createElement("div");
  divider.className = "history-divider";
  divider.textContent = "— Conversación anterior —";
  messagesEl.appendChild(divider);
  history.forEach(({ role, text }) => {
    const div = document.createElement("div");
    div.className = "msg " + role;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    div.appendChild(bubble);
    messagesEl.appendChild(div);
  });
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function connect(mode) {
  if (ws) { ws.onclose = null; ws.close(); }
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const pwParam = COACH_PW ? `&pw=${encodeURIComponent(COACH_PW)}` : "";
  ws = new WebSocket(`${proto}://${location.host}/api/coach/${sessionId}?mode=${mode}${pwParam}`);

  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === "limit_reached") {
      updateCounter();
      setResponding(false);
    } else if (msg.type === "start") {
      _agentBuf = "";
      addAgentBubble("");
    } else if (msg.type === "token") {
      _agentBuf += msg.text;
      appendToLastBubble(msg.text);
    } else if (msg.type === "end") {
      if (_agentBuf) {
        _history.push({ role: "agent", text: _agentBuf });
        saveHistory(currentMode, _history);
        updateClearBtn();
      }
      _agentBuf = "";
      setResponding(false);
      updateCounter();
    } else if (msg.type === "error") {
      appendToLastBubble("\\n[Error: " + msg.message + "]");
      _agentBuf = "";
      setResponding(false);
    }
  };

  ws.onclose = () => {
    setTimeout(() => { if (currentMode === mode) connect(mode); }, 2000);
  };
}

function setMode(mode) {
  currentMode = mode;
  sessionId   = getOrCreateSid(mode);
  _history    = loadHistory(mode);
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.toggle("active", b.dataset.mode === mode));
  setHint(mode);
  renderHistory(_history);
  updateClearBtn();
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
  _history.push({ role: "user", text });
  saveHistory(currentMode, _history);
  updateClearBtn();

  incrementDailyUsed();
  updateCounter();
  inputEl.value = "";
  inputEl.style.height = "auto";
  setResponding(true);
  ws.send(JSON.stringify({ message: text }));
}

clearBtn.addEventListener("click", () => {
  if (!confirm("¿Borrar el historial de este modo? Esta acción no se puede deshacer.")) return;
  _history = [];
  saveHistory(currentMode, _history);
  localStorage.removeItem(sidKey(currentMode));
  sessionId = getOrCreateSid(currentMode);
  messagesEl.innerHTML = "";
  updateClearBtn();
  connect(currentMode);
});

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
renderHistory(_history);
updateClearBtn();
updateCounter();
connect(currentMode);
</script>
</body>
</html>"""


@app.get("/health")
async def health():
    return {"status": "ok", "agent": settings.agent_name}


@app.get("/debug")
async def debug():
    """Diagnostic endpoint — checks config and connectivity."""
    import asyncio
    import anthropic as _anthropic
    import httpx
    from rag import vector_store as vs

    key = settings.anthropic_api_key
    key_status = "not set" if not key else f"set ({len(key)} chars, starts with {key[:8]}...)"

    # ChromaDB
    try:
        count = vs.count()
        chroma_status = f"ok ({count} vectors)"
    except Exception as e:
        chroma_status = f"error: {type(e).__name__}: {e}"

    import ssl, certifi

    # SSL version info
    ssl_info = ssl.OPENSSL_VERSION

    # Raw TCP (no TLS)
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection("api.anthropic.com", 443), timeout=10
        )
        writer.close()
        await writer.wait_closed()
        tcp_status = "ok"
    except Exception as e:
        tcp_status = f"error: {type(e).__name__}: {e}"

    # Direct HTTPS with default httpx (no SDK)
    try:
        async with httpx.AsyncClient(timeout=10) as hc:
            r = await hc.get("https://api.anthropic.com")
            https_default = f"ok (status={r.status_code})"
    except Exception as e:
        https_default = f"error: {type(e).__name__}: {e}"

    # Direct HTTPS with certifi + no proxy
    try:
        async with httpx.AsyncClient(trust_env=False, verify=certifi.where(), timeout=10) as hc:
            r = await hc.get("https://api.anthropic.com")
            https_certifi = f"ok (status={r.status_code})"
    except Exception as e:
        https_certifi = f"error: {type(e).__name__}: {e}"

    # Direct HTTPS with verify=False (skip SSL check)
    try:
        async with httpx.AsyncClient(verify=False, timeout=10) as hc:
            r = await hc.get("https://api.anthropic.com")
            https_nossl = f"ok (status={r.status_code})"
    except Exception as e:
        https_nossl = f"error: {type(e).__name__}: {e}"

    # Key whitespace check (trailing newline/space can corrupt Authorization header)
    key_clean = key.strip()
    key_had_whitespace = key != key_clean
    key_last_ord = ord(key[-1]) if key else 0

    # Direct POST to /v1/messages via httpx (no SDK) — tests if POST works at all
    post_status = "not tested"
    if key_clean:
        try:
            async with httpx.AsyncClient(timeout=15) as hc:
                r = await hc.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": key_clean,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={"model": "claude-haiku-4-5-20251001", "max_tokens": 5,
                          "messages": [{"role": "user", "content": "hi"}]},
                )
                post_status = f"ok (status={r.status_code})"
        except Exception as e:
            post_status = f"error: {type(e).__name__}: {e}"

    # Anthropic SDK — no custom http_client (SDK uses its own defaults)
    sdk_default = "not tested"
    if key_clean:
        try:
            client = _anthropic.AsyncAnthropic(api_key=key_clean)
            msg = await client.messages.create(
                model=settings.claude_model, max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
            sdk_default = f"ok (stop_reason={msg.stop_reason})"
        except Exception as e:
            sdk_default = f"error: {type(e).__name__}: {e}"

    return {
        "api_key": key_status,
        "key_had_whitespace": key_had_whitespace,
        "key_last_char_ord": key_last_ord,
        "ssl": ssl_info,
        "tcp_to_anthropic": tcp_status,
        "https_default": https_default,
        "https_certifi": https_certifi,
        "https_verify_false": https_nossl,
        "post_to_v1_messages": post_status,
        "chroma": chroma_status,
        "anthropic_sdk_default": sdk_default,
        "model": settings.claude_model,
    }
