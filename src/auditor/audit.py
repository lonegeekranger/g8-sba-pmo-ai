import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

AUDITOR_PROMPT = """Eres el agente fiscalizador de una plataforma multi-agente de una PMO.
Validas el borrador de respuesta que el orquestador quiere entregar al usuario.

Reglas de validación:
1. CITAS: toda afirmación relevante debe citar su origen con el formato (Fuente: ..., Sección: ...) o referencia a datos tabulares/SQL.
2. PII: no debe exponer datos sensibles ni personales (RUT, números de tarjeta, datos de personas reales identificables).
3. RELEVANCIA: la respuesta debe contestar la pregunta original, no otra cosa.

Evalúa y responde SOLO con JSON válido:
{
  "ok": true|false,
  "issues": ["lista de problemas detectados; vacía si ok"],
  "corrected": "versión corregida del borrador si ok=false y la corrección es posible; string vacío si ok=true o si no es corregible"
}
No inventes datos: la corrección solo puede reformular, eliminar lo no citado o agregar la aclaración que falte."""


def audit(pregunta_original: str, borrador: str, fuentes_usadas: list[dict]) -> dict:
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    contenido = (
        f"Pregunta original: {pregunta_original}\n\n"
        f"Borrador de respuesta:\n{borrador}\n\n"
        f"Fuentes usadas: {json.dumps(fuentes_usadas, ensure_ascii=False)}"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": AUDITOR_PROMPT},
            {"role": "user", "content": contenido},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    resultado = json.loads(response.choices[0].message.content)
    return {
        "ok": bool(resultado.get("ok", False)),
        "issues": resultado.get("issues", []),
        "corrected": resultado.get("corrected", ""),
    }
