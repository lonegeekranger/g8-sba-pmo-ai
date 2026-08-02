FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY src/ src/

ENV CHROMA_PATH=/mnt/vectordb
ENV PORT=8080

CMD ["sh", "-c", "uvicorn src.rag.serve:app --host 0.0.0.0 --port ${PORT}"]
