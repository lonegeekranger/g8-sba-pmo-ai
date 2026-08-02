from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from src.worker_sql.agent import ask

load_dotenv()

app = FastAPI(title="PMO-AI Worker SQL", version="0.1.0")


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
    return AskResponse(**ask(request.query))
