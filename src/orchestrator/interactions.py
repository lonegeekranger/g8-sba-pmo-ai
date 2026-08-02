import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.environ.get("INTERACTIONS_DB_PATH", ".interactions/interactions.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    tokens INTEGER,
    latency TEXT NOT NULL
);
"""


def _connect() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db() -> None:
    with _connect() as conn:
        conn.execute(SCHEMA)


def log_interaction(query: str, response: str, tokens: int, latency_ms: int) -> None:
    """Registra una interacción. Nunca lanza: un fallo de trazabilidad no debe
    romper la respuesta al usuario."""
    try:
        with _connect() as conn:
            conn.execute(SCHEMA)
            conn.execute(
                "INSERT INTO interactions (timestamp, query, response, tokens, latency) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    query,
                    response,
                    tokens,
                    str(latency_ms),
                ),
            )
    except Exception as e:
        print(f"[interactions] no se pudo registrar la interacción: {e}")


def get_stats() -> dict:
    """Agregados de la tabla interactions. Nunca expone query/response individuales."""
    row = (0, 0, 0, 0, 0, 0, None, None)
    try:
        with _connect() as conn:
            conn.execute(SCHEMA)
            row = conn.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(tokens), 0),
                    COALESCE(AVG(tokens), 0),
                    COALESCE(AVG(CAST(latency AS INTEGER)), 0),
                    COALESCE(MIN(CAST(latency AS INTEGER)), 0),
                    COALESCE(MAX(CAST(latency AS INTEGER)), 0),
                    MIN(timestamp),
                    MAX(timestamp)
                FROM interactions
                """
            ).fetchone()
    except Exception as e:
        print(f"[interactions] no se pudo leer estadísticas: {e}")

    total, total_tokens, avg_tokens, avg_latency, min_latency, max_latency, first_ts, last_ts = row
    return {
        "total_interactions": total,
        "total_tokens": total_tokens,
        "avg_tokens": round(avg_tokens, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "min_latency_ms": min_latency,
        "max_latency_ms": max_latency,
        "first_interaction": first_ts,
        "last_interaction": last_ts,
    }
