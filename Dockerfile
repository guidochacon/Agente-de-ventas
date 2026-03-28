FROM python:3.11-slim

WORKDIR /app

# System deps for chromadb, lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-download and warm-up ChromaDB ONNX embedding model so it's baked into the image
# Must actually call ef() to trigger the lazy model download (not just instantiate the class)
RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; ef = DefaultEmbeddingFunction(); ef(['warm up']); print('ONNX model ready')"

COPY backend/ ./backend/
COPY start.sh ./start.sh
RUN chmod +x start.sh

# Ingest knowledge base at build time — data is baked into the image,
# instantly available at runtime with no event loop blocking
RUN cd /app/backend && python -u scripts/ingest_all.py

EXPOSE 8000
CMD ["bash", "start.sh"]
