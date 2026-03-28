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
# Must actually call the function to trigger the model download (lazy download on first __call__)
RUN python -c "
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
ef = DefaultEmbeddingFunction()
ef(['warm up'])
print('ONNX model downloaded and ready')
"

COPY backend/ ./backend/
COPY start.sh ./start.sh
RUN chmod +x start.sh

EXPOSE 8000
CMD ["bash", "start.sh"]
