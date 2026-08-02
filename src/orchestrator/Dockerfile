# Build context: raíz del repo
#   docker build -f src/orchestrator/Dockerfile -t pmo-ai-orchestrator .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/__init__.py src/__init__.py
COPY src/orchestrator/ src/orchestrator/

ENV PORT=8080

CMD ["sh", "-c", "uvicorn src.orchestrator.serve:app --host 0.0.0.0 --port ${PORT}"]
