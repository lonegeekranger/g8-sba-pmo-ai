import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from src.orchestrator.clients import (
    auditor_url,
    call_auditor,
    call_worker,
    worker_rag_url,
    worker_sql_url,
)
from src.orchestrator.interactions import get_stats, init_db, log_interaction
from src.orchestrator.router import decide_route

load_dotenv()

app = FastAPI(title="PMO-AI Orquestador", version="0.1.0")
init_db()


class AskRequest(BaseModel):
    query: str


class Source(BaseModel):
    fuente: str
    seccion: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    ruta: str
    workers_usados: list[str]
    fiscalizacion: dict | None
    latency_ms: int
    tokens: int


class StatsResponse(BaseModel):
    total_interactions: int
    total_tokens: int
    avg_tokens: float
    avg_latency_ms: float
    min_latency_ms: int
    max_latency_ms: int
    first_interaction: str | None
    last_interaction: str | None


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "workers": {
            "rag": worker_rag_url(),
            "sql": worker_sql_url(),
            "auditor": auditor_url(),
        },
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    start = time.time()
    decision = decide_route(request.query)
    ruta = decision.get("ruta", "semantic")
    workers_usados = []
    notas = []

    respuesta_rag = None
    if ruta in ("semantic", "both"):
        if worker_rag_url():
            respuesta_rag = call_worker(worker_rag_url(), request.query)
            workers_usados.append("rag")
        else:
            notas.append("worker RAG no configurado")

    respuesta_sql = None
    if ruta in ("sql", "both"):
        if worker_sql_url():
            respuesta_sql = call_worker(worker_sql_url(), request.query)
            workers_usados.append("sql")
        else:
            notas.append("worker SQL aún no disponible; se respondió con fuentes documentales")
            if respuesta_rag is None and worker_rag_url():
                respuesta_rag = call_worker(worker_rag_url(), request.query)
                workers_usados.append("rag")

    sources = []
    partes = []
    if respuesta_rag:
        partes.append(respuesta_rag["answer"])
        sources.extend(respuesta_rag.get("sources", []))
    if respuesta_sql:
        partes.append(f"Datos tabulares:\n{respuesta_sql['answer']}")
        sources.extend(respuesta_sql.get("sources", []))
    if not partes:
        partes.append("No hay workers disponibles para responder esta consulta.")

    borrador = "\n\n".join(partes)
    if notas:
        borrador += "\n\n_Nota del orquestador: " + "; ".join(notas) + "_"

    fiscalizacion = None
    answer = borrador
    if auditor_url():
        fiscalizacion = call_auditor(auditor_url(), request.query, borrador, sources)
        if not fiscalizacion.get("ok", True) and fiscalizacion.get("corrected"):
            answer = fiscalizacion["corrected"]

    tokens = decision.get("tokens", 0)
    if respuesta_rag:
        tokens += respuesta_rag.get("tokens", 0)
    if respuesta_sql:
        tokens += respuesta_sql.get("tokens", 0)
    if fiscalizacion:
        tokens += fiscalizacion.get("tokens", 0)

    latency_ms = int((time.time() - start) * 1000)
    log_interaction(request.query, answer, tokens, latency_ms)

    return AskResponse(
        answer=answer,
        sources=[Source(**s) for s in sources],
        ruta=ruta,
        workers_usados=workers_usados,
        fiscalizacion=fiscalizacion,
        latency_ms=latency_ms,
        tokens=tokens,
    )


@app.get("/stats", response_model=StatsResponse)
def stats() -> StatsResponse:
    return StatsResponse(**get_stats())
