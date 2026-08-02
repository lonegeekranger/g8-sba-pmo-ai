import os

import requests

TIMEOUT = 60


def call_worker(base_url: str, query: str) -> dict:
    response = requests.post(
        f"{base_url.rstrip('/')}/ask",
        json={"query": query},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def call_auditor(base_url: str, pregunta: str, borrador: str, fuentes: list[dict]) -> dict:
    response = requests.post(
        f"{base_url.rstrip('/')}/audit",
        json={"pregunta_original": pregunta, "borrador": borrador, "fuentes_usadas": fuentes},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def worker_rag_url() -> str | None:
    return os.environ.get("WORKER_RAG_URL")


def worker_sql_url() -> str | None:
    return os.environ.get("WORKER_SQL_URL")


def auditor_url() -> str | None:
    return os.environ.get("AUDITOR_URL")
