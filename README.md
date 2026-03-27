# Agente de Ventas con IA

Agente de ventas conversacional con RAG, captura de leads, agendado y cotizaciones.

## Inicio rápido

### 1. Configurar variables de entorno

```bash
cd backend
cp .env.example .env
# Editar .env con tus API keys
```

### 2. Instalar dependencias

```bash
cd backend
pip install -r requirements.txt
```

### 3. Ingerir tu base de conocimiento

```bash
# Colocar archivos .txt, .md, .pdf en backend/knowledge_base/
# Luego ejecutar:
python scripts/ingest_all.py
```

### 4. Levantar el servidor

```bash
uvicorn main:app --reload
```

### 5. Abrir el demo

Ir a: http://localhost:8000

---

## Embedding en tu sitio web

```html
<script>
  window.SalesAgentConfig = {
    agentUrl: "https://tu-backend.com",
    agentName: "Alex",
    primaryColor: "#2563EB",
    welcomeMessage: "¡Hola! ¿En qué puedo ayudarte hoy?",
    collectLeadAfterMessages: 2
  };
</script>
<script src="https://tu-backend.com/widget/sales-agent-widget.min.js" async></script>
```

---

## Agregar conocimiento al agente

### Desde el admin
1. Ir a http://localhost:8000/admin
2. Pegar la URL de tu sitio web
3. O subir un PDF

### Desde la API

```bash
# Texto
curl -X POST http://localhost:8000/api/knowledge/ingest/text \
  -H "Content-Type: application/json" \
  -d '{"name": "Servicios", "content": "Descripción de tu servicio..."}'

# URL
curl -X POST http://localhost:8000/api/knowledge/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://tusitio.com/servicios"}'

# PDF
curl -X POST http://localhost:8000/api/knowledge/ingest/pdf \
  -F "file=@tu-documento.pdf"
```

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `ANTHROPIC_API_KEY` | API Key de Anthropic | Sí |
| `AGENT_NAME` | Nombre del agente (ej: Alex) | No |
| `AGENT_BUSINESS_NAME` | Nombre de tu empresa | No |
| `CALENDLY_API_KEY` | Para agendado de citas | No |
| `SENDGRID_API_KEY` | Para envío de cotizaciones | No |

---

## Docker

```bash
cd docker
docker-compose up -d
```

---

## Endpoints principales

| Endpoint | Descripción |
|---|---|
| `GET /` | Página demo con widget |
| `GET /admin` | Panel de administración |
| `WS /api/chat/{session_id}` | Chat WebSocket |
| `GET /api/leads` | Lista de leads |
| `GET /api/leads/export` | Exportar leads CSV |
| `POST /api/knowledge/ingest/text` | Ingerir texto |
| `POST /api/knowledge/ingest/url` | Ingerir URL |
| `POST /api/knowledge/ingest/pdf` | Ingerir PDF |
| `GET /api/knowledge` | Listar documentos KB |
| `GET /api/quotes/{id}/pdf` | Descargar cotización |
