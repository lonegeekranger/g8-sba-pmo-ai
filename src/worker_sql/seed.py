import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "proyecto.db"

SCHEMA = """
DROP TABLE IF EXISTS hitos;
DROP TABLE IF EXISTS riesgos;
DROP TABLE IF EXISTS metricas;
DROP TABLE IF EXISTS presupuesto;

CREATE TABLE hitos (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    fecha_baseline TEXT NOT NULL,
    fecha_real_proyectada TEXT NOT NULL,
    estado TEXT NOT NULL
);

CREATE TABLE riesgos (
    id TEXT PRIMARY KEY,
    descripcion TEXT NOT NULL,
    probabilidad TEXT NOT NULL,
    impacto TEXT NOT NULL,
    exposicion TEXT NOT NULL,
    dueno TEXT NOT NULL
);

CREATE TABLE metricas (
    nombre TEXT PRIMARY KEY,
    valor REAL NOT NULL,
    unidad TEXT NOT NULL,
    comentario TEXT
);

CREATE TABLE presupuesto (
    partida TEXT PRIMARY KEY,
    aprobado_mm REAL NOT NULL,
    ejecutado_mm REAL NOT NULL,
    pct_ejecutado REAL NOT NULL
);
"""

HITOS = [
    ("H1", "Charter aprobado y equipo constituído", "2026-01-30", "2026-01-30", "Completado"),
    ("H2", "Levantamiento de recetas de obra y reglas de negocio", "2026-03-13", "2026-03-27", "Completado con atraso"),
    ("H3", "Pipeline de datos ConstruCard en producción", "2026-04-17", "2026-05-08", "Completado con atraso"),
    ("H4", "Modelo MVP con precisión@5 >= 0,62", "2026-05-29", "2026-06-05", "Completado"),
    ("H5", "Integración app y e-commerce en ambiente QA", "2026-07-10", "2026-07-24", "Completado con atraso"),
    ("H6", "Integración kioscos ObraDirecta (piloto 6 locales)", "2026-08-07", "2026-08-28", "Vencido"),
    ("H7", "Pruebas de carga y pentesting", "2026-08-21", "2026-09-04", "En riesgo"),
    ("H8", "Aprobación de Cumplimiento (datos ConstruCard)", "2026-08-28", "2026-09-11", "En riesgo"),
    ("H9", "Go-live canal digital (app + e-commerce)", "2026-09-07", "2026-09-21", "Deslizado"),
    ("H10", "Go-live kioscos ObraDirecta (74 locales)", "2026-09-07", "2026-10-05", "Deslizado"),
]

RIESGOS = [
    ("R-01", "Firmware de kioscos ObraDirecta (v3.2) no soporta el cliente embebido; actualización requiere visita técnica a 74 locales", "Alta", "Alto", "Crítico", "S. Rojas"),
    ("R-02", "Cumplimiento objeta el uso de historial ConstruCard para perfiles de menores de edad en cuentas familiares", "Media", "Alto", "Alto", "I. Herrera"),
    ("R-03", "Conflicto de función objetivo: ponderación de margen (marca propia) vs. relevancia técnica sin definición formal", "Alta", "Medio", "Alto", "A. Solís / M. Fuentes"),
    ("R-04", "Desplazamiento de marcas líderes gatilla retiro de inversión publicitaria de 3 proveedores con retail media comprometido", "Media", "Medio", "Medio", "C. Reyes"),
    ("R-05", "Latencia p95 supera SLA en horario peak de kioscos (sábado 10:00-14:00)", "Media", "Medio", "Medio", "S. Rojas"),
    ("R-06", "Solo 2 personas conocen el modelo de recetas en el equipo de Categorías", "Media", "Alto", "Alto", "M. Fuentes"),
    ("R-07", "Entrada de ToolShare Brasil (8 locales, octubre 2026) presiona a adelantar go-live sacrificando pruebas", "Baja", "Alto", "Medio", "I. Herrera"),
]

METRICAS = [
    ("SPI", 0.89, "índice", "Tendencia a la baja por H6"),
    ("CPI", 1.02, "índice", "En rango; despliegue OTA agregaría ~CLP $38 MM"),
    ("defectos_criticos", 3, "cantidad", "Los 3 críticos son del cliente de kiosco"),
    ("defectos_mayores", 17, "cantidad", None),
    ("defectos_menores", 42, "cantidad", None),
    ("cobertura_pruebas", 78, "porcentaje", "Meta de go-live: 85%"),
    ("precision5_digital", 0.64, "índice", "Con ponderación técnica pura"),
    ("precision5_obradirecta", 0.55, "índice", "Bajo umbral de aceptación 0,60 por ponderación 2x marca propia"),
    ("latencia_p95_ms", 690, "ms", "Dentro de SLA 800 ms; pendiente prueba full con 74 kioscos"),
    ("horas_consumidas", 6940, "horas", "De 9.200 planificadas (75,4%)"),
    ("satisfaccion_sponsor", 3.1, "sobre 5", "Cayó desde 4,2 en mayo por deslizamiento del go-live"),
]

PRESUPUESTO = [
    ("Equipo interno (horas)", 620, 468, 75.5),
    ("Consultora de datos (DataAndes SpA)", 480, 351, 73.1),
    ("Infraestructura GCP (18 meses)", 210, 122, 58.1),
    ("Licencias y herramientas", 130, 98, 75.4),
    ("Hardware kioscos (adaptadores, pruebas)", 180, 96, 53.3),
    ("Contingencia", 220, 141.4, 64.3),
]


def seed() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO hitos VALUES (?,?,?,?,?)", HITOS)
        conn.executemany("INSERT INTO riesgos VALUES (?,?,?,?,?,?)", RIESGOS)
        conn.executemany("INSERT INTO metricas VALUES (?,?,?,?)", METRICAS)
        conn.executemany("INSERT INTO presupuesto VALUES (?,?,?,?)", PRESUPUESTO)
    print(f"Base creada en {DB_PATH}: {len(HITOS)} hitos, {len(RIESGOS)} riesgos, {len(METRICAS)} métricas, {len(PRESUPUESTO)} partidas")


if __name__ == "__main__":
    seed()
