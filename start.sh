#!/bin/bash
set -e

cd /app/backend

echo "=== Iniciando Agente de Ventas - Scaling In Blue ==="
echo "Ingiriendo knowledge base..."
python scripts/ingest_all.py

echo "Levantando servidor en puerto ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
