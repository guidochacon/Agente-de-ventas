FROM python:3.11-slim

WORKDIR /app

# System deps for chromadb (onnxruntime), lxml, weasyprint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/
COPY start.sh ./start.sh
RUN chmod +x start.sh

EXPOSE 8000
CMD ["bash", "start.sh"]
