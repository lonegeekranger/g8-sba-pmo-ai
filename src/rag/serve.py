from fastapi import FastAPI
from pydantic import BaseModel

from src.rag.query import ask

app = FastAPI(title="PMO-AI", version="0.1.0")


class AskRequest(BaseModel):
    query: str


class Source(BaseModel):
    fuente: str
    seccion: str


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(request: AskRequest) -> AskResponse:
    result = ask(request.query)
    return AskResponse(**result)
