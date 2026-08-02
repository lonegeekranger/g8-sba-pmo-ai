# Worker 2 — Consulta SQL (text-to-SQL)

**Curso:** Simulación Basada en Agentes — Programa de Inteligencia Artificial, UAI
**Fecha:** Agosto 2026
**Estado:** Construido y verificado localmente — pendiente de despliegue
**Rol en la plataforma:** Worker 2 de 4 agentes (ver `masterplan.md`) — atiende las consultas de datos tabulares que le delega el Orquestador (paso 4 del roadmap)

---

## 1. Qué es este agente

Worker especializado en **consultas estructuradas sobre los datos del proyecto**: conteos, totales, promedios, listados y comparaciones numéricas. Mientras el Worker RAG responde "qué dicen los documentos", este worker responde "qué dicen los números". Implementa el patrón **text-to-SQL**: el usuario pregunta en lenguaje natural, DeepSeek genera la consulta SQL, se ejecuta contra una base SQLite y la respuesta se redacta citando los datos exactos obtenidos.

## 2. Flujo

```
Pregunta en lenguaje natural
   │
   ├─ 1. Generación SQL (DeepSeek, temperatura 0, salida JSON)
   │     prompt = esquema de las 4 tablas + reglas estrictas
   │     → {"sql": "SELECT ...", "explicacion": "..."}
   │
   ├─ 2. Guard de seguridad: solo SELECT de una sentencia
   │     → se ejecuta en modo read-only (SQLite URI mode=ro)
   │
   ├─ 3. Redacción de respuesta (DeepSeek, temperatura 0.2)
   │     solo con las filas obtenidas; prohibido inventar datos
   │
   └─ 4. Respuesta: {answer (incluye el SQL ejecutado), sources}
```

## 3. Datos: de documento a tablas

El documento PMO `PMO-FER-2025-014_motor_recomendacion_proyecto_completo.md` contiene 4 tablas markdown que se transformaron en tablas relacionales (`seed.py`):

| Tabla | Filas | Contenido |
|---|---|---|
| `hitos` | 10 | id, nombre, fecha_baseline, fecha_real_proyectada, estado |
| `riesgos` | 7 | id, descripción, probabilidad, impacto, exposición, dueño |
| `metricas` | 11 | nombre, valor, unidad, comentario (SPI, CPI, defectos, cobertura, precisión@5, latencia, horas, satisfacción) |
| `presupuesto` | 6 | partida, aprobado_mm, ejecutado_mm, pct_ejecutado (montos en millones CLP) |

La base SQLite se genera **en el build de la imagen Docker** (`RUN python -m src.worker_sql.seed`): los datos son estáticos y viajan dentro del contenedor, sin dependencias externas.

## 4. Decisiones de diseño

| Decisión | Detalle | Razón |
|---|---|---|
| Guard de solo-SELECT | Se rechaza todo lo que no sea una única sentencia `SELECT` (sin `;` internos) y la conexión se abre en modo `mode=ro` | Doble capa contra SQL malicioso o destructivo generado por el LLM |
| Temperatura 0 en la generación SQL | La consulta debe ser reproducible | La misma pregunta genera el mismo SQL |
| SQL visible en la respuesta | La respuesta incluye `_SQL ejecutado: ..._` | Trazabilidad: el usuario (y el profesor) puede verificar exactamente qué se consultó |
| Manejo de errores explícito | Si el SQL falla, la respuesta declara el error y muestra el SQL intentado | El orquestador y el fiscalizador reciben información honesta, no una respuesta inventada |
| SQLite embebido | Sin servidor de base de datos | Suficiente para datos estáticos del curso; la migración natural es Cloud SQL si los datos crecen o se actualizan |

## 5. Verificación local

| Consulta de prueba | SQL generado | Resultado |
|---|---|---|
| "¿cuántos hitos están vencidos o en riesgo?" | `SELECT COUNT(*) FROM hitos WHERE estado IN ('Vencido','En riesgo')` | **3** (correcto: H6 vencido, H7 y H8 en riesgo) |
| "¿cuántos riesgos de exposición crítica o alta hay?" | `SELECT ... FROM riesgos WHERE exposicion IN ('Crítico','Alto')` | **4** (correcto: R-01, R-02, R-03, R-06) |
| Consulta vía orquestador (ruta `sql`) | — | Respuesta integrada y fiscalizada correctamente |

## 6. Limitaciones conocidas

1. **Datos estáticos:** actualizar los datos exige editar `seed.py` y redesplegar. Un pipeline de sincronización desde los documentos (o una fuente transaccional) es el paso natural.
2. **`interactions` vive en el orquestador, no aquí:** el paso 7 del roadmap (trazabilidad) se implementó como una tabla separada, escrita por el orquestador — este worker solo aporta sus `tokens` a la suma total (ver `src/orchestrator/AGENTE.md`).
3. **Esquema pequeño:** preguntas que crucen documentos y tablas (ej. "compara lo que dice el documento con los números") dependen de que el orquestador use la ruta `both` y el fiscalizador unifique, como se verificó en la integración.
4. **Un solo dialecto:** el prompt está afinado para SQLite; migrar a Postgres requiere ajustar el esquema descrito en el prompt.

## 7. Cómo probarlo localmente

```bash
uv run python -m src.worker_sql.seed     # genera src/worker_sql/proyecto.db
uv run uvicorn src.worker_sql.serve:app --port 8082

curl -X POST localhost:8082/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "¿qué partida del presupuesto va más ejecutada en porcentaje?"}'
```
