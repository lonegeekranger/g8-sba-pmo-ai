import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DB_PATH = Path(os.environ.get("SQL_DB_PATH", Path(__file__).parent / "proyecto.db"))

SCHEMA_DESC = """
Tablas disponibles (base SQLite del proyecto PMO-FER-2025-014):

hitos(id, nombre, fecha_baseline, fecha_real_proyectada, estado)
  - estados posibles: 'Completado', 'Completado con atraso', 'Vencido', 'En riesgo', 'Deslizado'
riesgos(id, descripcion, probabilidad, impacto, exposicion, dueno)
  - exposicion: 'Crítico', 'Alto', 'Medio'
metricas(nombre, valor, unidad, comentario)
  - nombres: SPI, CPI, defectos_criticos, defectos_mayores, defectos_menores, cobertura_pruebas,
    precision5_digital, precision5_obradirecta, latencia_p95_ms, horas_consumidas, satisfaccion_sponsor
presupuesto(partida, aprobado_mm, ejecutado_mm, pct_ejecutado)
  - montos en millones de CLP
"""

SQL_PROMPT = f"""Eres un generador de SQL para SQLite. A partir de la pregunta del usuario, genera UNA sola consulta SELECT.

{SCHEMA_DESC}

Reglas:
- Solo SELECT. Jamás INSERT/UPDATE/DELETE/DROP.
- Responde SOLO con JSON válido: {{"sql": "...", "explicacion": "qué obtiene la consulta"}}"""

ANSWER_PROMPT = """Eres un analista de PMO. Redacta una respuesta concisa en español a la pregunta del usuario,
basándote SOLO en las filas entregadas. Menciona las cifras exactas. Al final, indica entre paréntesis
(Fuente: datos tabulares del proyecto, Consulta SQL). No inventes datos que no estén en las filas."""


def generar_sql(query: str) -> dict:
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": SQL_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    resultado = json.loads(response.choices[0].message.content)
    resultado["tokens"] = response.usage.total_tokens if response.usage else 0
    return resultado


def ejecutar_sql(sql: str) -> list[dict]:
    normalizado = sql.strip().rstrip(";")
    if not normalizado.upper().startswith("SELECT") or ";" in normalizado:
        raise ValueError(f"Consulta rechazada (solo SELECT de una sentencia): {sql}")
    uri = f"file:{DB_PATH}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(normalizado)
        return [dict(row) for row in cursor.fetchall()]


def redactar_respuesta(query: str, filas: list[dict], sql: str) -> tuple[str, int]:
    client = OpenAI(
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url="https://api.deepseek.com",
    )
    contenido = (
        f"Pregunta: {query}\n\n"
        f"Filas obtenidas:\n{json.dumps(filas, ensure_ascii=False, indent=2)}"
    )
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            {"role": "user", "content": contenido},
        ],
        temperature=0.2,
    )
    tokens = response.usage.total_tokens if response.usage else 0
    return response.choices[0].message.content, tokens


def ask(query: str) -> dict:
    generado = generar_sql(query)
    sql = generado["sql"]
    tokens = generado.get("tokens", 0)
    try:
        filas = ejecutar_sql(sql)
    except Exception as e:
        return {
            "answer": f"No pude ejecutar la consulta generada ({e}). SQL intentado: {sql}",
            "sources": [{"fuente": "datos_tabulares_proyecto", "seccion": "error SQL"}],
            "tokens": tokens,
        }
    answer, tokens_respuesta = redactar_respuesta(query, filas, sql)
    return {
        "answer": f"{answer}\n\n_SQL ejecutado: `{sql}`_",
        "sources": [{"fuente": "datos_tabulares_proyecto", "seccion": f"SQL: {sql[:80]}"}],
        "tokens": tokens + tokens_respuesta,
    }
