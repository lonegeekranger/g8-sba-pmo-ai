from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from src.auditor.audit import audit

load_dotenv()

app = FastAPI(title="PMO-AI Fiscalizador", version="0.1.0")


class AuditRequest(BaseModel):
    pregunta_original: str
    borrador: str
    fuentes_usadas: list[dict]


class AuditResponse(BaseModel):
    ok: bool
    issues: list[str]
    corrected: str
    tokens: int = 0


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/audit", response_model=AuditResponse)
def audit_endpoint(request: AuditRequest) -> AuditResponse:
    resultado = audit(request.pregunta_original, request.borrador, request.fuentes_usadas)
    return AuditResponse(**resultado)
