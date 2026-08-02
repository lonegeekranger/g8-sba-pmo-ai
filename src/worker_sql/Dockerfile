# Build context: raíz del repo
#   docker build -f src/worker_sql/Dockerfile -t pmo-ai-worker-sql .
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/__init__.py src/__init__.py
COPY src/worker_sql/ src/worker_sql/

RUN python -m src.worker_sql.seed

ENV SQL_DB_PATH=/app/src/worker_sql/proyecto.db
ENV PORT=8080

CMD ["sh", "-c", "uvicorn src.worker_sql.serve:app --host 0.0.0.0 --port ${PORT}"]
