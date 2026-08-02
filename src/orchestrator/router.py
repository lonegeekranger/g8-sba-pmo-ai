import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ROUTER_PROMPT = """Eres el router de un sistema multi-agente de una PMO de proyectos TI.
Debes decidir a qué worker(s) delegar cada consulta del usuario.

Workers disponibles:
- semantic: búsqueda semántica sobre documentos PMO (estado de proyectos, riesgos, hitos, métricas descritas en reportes, decisiones, bitácoras).
- sql: consultas sobre datos tabulares (conteos, totales, promedios, listados de registros, comparaciones numéricas).

Criterios:
- Pregunta sobre contenido de documentos ("qué dice", "estado", "riesgos", "hitos", "explica") → semantic
- Pregunta de datos numéricos o registros ("cuántos", "total", "promedio", "lista los") → sql
- Si combina ambas → both
- Si no está claro → semantic (la documentación es la fuente primaria)

Responde SOLO con JSON válido: {"ruta": "semantic"|"sql"|"both", "razon": "..."}"""


def decide_route(query: str) -> dict:
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
