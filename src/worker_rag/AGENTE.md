# Worker 1 — Búsqueda Semántica (RAG de Consulta PMO)

**Curso:** Simulación Basada en Agentes — Programa de Inteligencia Artificial, UAI
**Fecha:** Agosto 2026
**Estado:** Desplegado y operativo
**Rol en la plataforma:** Worker 1 de 4 agentes (ver `masterplan.md`) — atiende las consultas documentales que le delega el Orquestador

---

## 1. Qué es este agente

Es el **primer worker de la plataforma PMO-AI**: un agente especializado en **preguntas y respuestas sobre documentación de proyectos TI**, construido con el patrón RAG (Retrieval-Augmented Generation). Permite consultar en lenguaje natural el estado del portafolio, hitos vencidos, alertas de riesgo, métricas de desempeño y presupuesto, con **respuestas trazables**: cada afirmación cita el documento fuente y la sección de origen, como exige el diseño del proyecto.

En la arquitectura final (4 agentes: Orquestador, Worker Semántico, Worker SQL, Fiscalizador), este worker responde a las consultas de tipo documental que le delega el Orquestador. Hoy opera de forma standalone detrás de su propio endpoint; cuando el Orquestador exista, este servicio quedará como su backend de búsqueda semántica.

**Endpoint público:** `https://pmo-ai-101547847876.southamerica-west1.run.app`

```
POST /ask      {"query": "¿qué hitos están vencidos?"}  →  {"answer": ..., "sources": [...]}
GET  /health   →  {"status": "ok"}
```

## 2. Arquitectura

```
Usuario → POST /ask (FastAPI en Cloud Run, Santiago)
             │
             ├─ 1. Embedding de la pregunta (Vertex AI text-embedding-004)
             ├─ 2. Búsqueda k=5 en base vectorial (Chroma, persistida en GCS)
             └─ 3. Generación con los 5 chunks como contexto (DeepSeek chat)
                    → respuesta + citas (fuente, sección)
```

| Componente | Elección | Justificación |
|---|---|---|
| Chunking | Python puro, split por headers `##` de markdown | Los documentos PMO son `.md` con secciones numeradas; chunkear por sección preserva la unidad semántica y permite citar la sección exacta. Chunks de ~800 caracteres con overlap de 150 |
| Embeddings | Vertex AI `text-embedding-004` (768 dims) | Nativo GCP, autenticación por service account, sin APIs adicionales |
| Base vectorial | Chroma (embebida, persistente) | Permitida por el roadmap; no requiere administrar un servidor separado |
| Persistencia del índice | Bucket GCS montado como volumen (Cloud Storage FUSE) en Cloud Run | El índice sobrevive redespliegues sin reconstruir la imagen |
| LLM de generación | DeepSeek (`deepseek-chat`), API compatible OpenAI, temperatura 0.2 | Convención del proyecto; baja temperatura para respuestas fieles al contexto |
| Servicio | FastAPI + uvicorn en Cloud Run | Entregable final del taller: URL pública |

## 3. Cómo se cargan los datos

El primer documento cargado es `data/PMO-FER-2025-014_motor_recomendacion_proyecto_completo.md` (reporte PMO de un proyecto de motor de recomendación para retail). El pipeline es:

1. `chunk.py` divide el documento por secciones → **22 chunks**, cada uno con metadata `{fuente, seccion, fecha_carga}`
2. `embed.py` vectoriza los chunks con Vertex AI (task type `RETRIEVAL_DOCUMENT`)
3. `load.py` hace upsert a la colección `pmo_docs` de Chroma
4. El índice local se sincroniza al bucket (`gsutil cp -r .chroma/* gs://pmo-ai-vectordb/chroma/`), desde donde Cloud Run lo monta

Agregar un nuevo proyecto al RAG = copiar un `.md` a `data/` y repetir el paso 3-4. No hay que tocar código.

## 4. Trazabilidad: la decisión de diseño central

El system prompt obliga al modelo a responder **solo con base en el contexto recuperado** y a citar cada afirmación con el formato `(Fuente: <archivo>, Sección: <sección>)`. La metadata de sección viaja desde el chunking hasta el prompt, por lo que la cita es verificable contra el documento original. Esto cumple dos objetivos del proyecto: transparencia para el usuario de la PMO y auditabilidad de las respuestas del agente.

## 5. Infraestructura GCP

- **Proyecto:** `pmo-ai-504313` — **Región:** `southamerica-west1` (Santiago)
- **Service account** `pmo-ai-sa` con privilegios mínimos: `aiplatform.user`, `secretmanager.secretAccessor` y `objectAdmin` solo sobre el bucket del índice
- **Secret Manager** guarda la API key de DeepSeek; Cloud Run la inyecta como variable de entorno, nunca va en código ni en el repo
- **Deploy:** `gcloud run deploy --source .` con Dockerfile (python:3.12-slim + uv)

**Decisión regional relevante:** los modelos de embeddings de Vertex AI no están disponibles en `southamerica-west1`. Solo el endpoint de vectorización corre en `us-central1` (variable `EMBED_REGION`); el texto viaja para vectorizarse pero no se almacena fuera de región. Bucket, Cloud Run y secretos permanecen en Santiago.

## 6. Resultados de validación

Se probaron 5 consultas reales contra el endpoint público:

| Consulta | Secciones recuperadas | ¿Citas correctas? |
|---|---|---|
| Estado del portafolio | 4. Hitos, 6. Métricas, 11. Bitácora, 12. Próximos hitos | Sí |
| Hitos vencidos | 4. Hitos, 5. Riesgos | Sí — identifica H6 como único vencido y distingue "en riesgo" de "vencido" |
| Alertas de riesgo | 5. Riesgos activos, 4. Hitos | Sí — ordena por exposición (R-01 crítico primero) |
| Métricas de desempeño | 6. Métricas, 1. Ficha, 4. Hitos | Sí — reporta SPI 0,89 y CPI 1,02 exactos |
| Presupuesto ejecutado | 7. Presupuesto, 1. Ficha | Sí — 69,3% y desglose por partida exactos |

- **Latencia:** ~2,5–3,5 s por consulta (instancia warm)
- **Costo estimado por 1.000 consultas:** < US$1 (embeddings ~US$0,01 + DeepSeek ~US$0,10–0,20 + Cloud Run ~US$0,50)

## 7. Limitaciones conocidas

1. **Chroma sobre GCS FUSE:** Chroma usa SQLite internamente, que no tolera bien escrituras concurrentes sobre FUSE. Aceptable con 1 instancia y patrón de lectura; si el sistema crece, la migración natural es a pgvector (Cloud SQL) o Qdrant.
2. **Actualización del índice es manual:** agregar un documento requiere correr el loader y sincronizar el bucket. Un Cloud Run Job o un trigger sobre el bucket automatizaría este paso.
3. **Sin memoria conversacional:** cada consulta es independiente (esto es distinto de la tabla `interactions`, que sí registra el historial de consultas al orquestador — ver `src/orchestrator/AGENTE.md`).

## 8. Próximos pasos (roadmap del taller)

- Worker de consulta SQL y agente orquestador con criterios de delegación (paso 3-4)
- Agente fiscalizador que valide citas, detecte PII y verifique que la respuesta conteste la pregunta (paso 5)
- Evaluación de re-ranking / hybrid search sobre el retriever actual (paso 6)

## 9. Cómo probarlo

```bash
curl -X POST https://pmo-ai-101547847876.southamerica-west1.run.app/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "¿cuáles son las principales alertas de riesgo del proyecto?"}'
```

Localmente:

```bash
uv pip install -r requirements.txt
uv run python -m src.worker_rag.load data/          # carga documentos al índice
uv run python -m src.worker_rag.query "¿pregunta?"  # consulta por CLI
uv run uvicorn src.worker_rag.serve:app --port 8080 # API local
```
