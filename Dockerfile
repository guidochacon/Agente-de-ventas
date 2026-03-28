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

COPY backend/ ./backend/
COPY start.sh ./start.sh
RUN chmod +x start.sh

EXPOSE 8000
CMD ["bash", "start.sh"]
