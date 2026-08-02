# Build context: raíz del repo
#   docker build -f src/auditor/Dockerfile -t pmo-ai-auditor .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/__init__.py src/__init__.py
COPY src/auditor/ src/auditor/

ENV PORT=8080

CMD ["sh", "-c", "uvicorn src.auditor.serve:app --host 0.0.0.0 --port ${PORT}"]
