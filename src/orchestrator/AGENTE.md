# Agente Orquestador — PMO-AI

**Curso:** Simulación Basada en Agentes — Programa de Inteligencia Artificial, UAI
**Fecha:** Agosto 2026
**Estado:** Construido y verificado localmente — pendiente de despliegue
**Rol en la plataforma:** Agente 1 de 4 (ver `masterplan.md`) — punto de entrada único del usuario; decide la delegación y compone la respuesta final

---

## 1. Qué es este agente

El orquestador es la **puerta de entrada de la plataforma PMO-AI**. No responde preguntas por sí mismo: recibe la consulta del usuario, decide a qué worker(s) especializados delegarla, fusiona sus resultados en un borrador único y lo envía al fiscalizador antes de entregarlo. Corresponde al paso 3 del roadmap del taller (rol y system prompt, lista de workers, criterios de delegación, formato de salida estándar).

## 2. Flujo de una consulta

```
Usuario → POST /ask
   │
   ├─ 1. Router (DeepSeek, temperatura 0, salida JSON)
   │     → {"ruta": "semantic" | "sql" | "both", "razon": "..."}
   │
   ├─ 2. Delegación HTTP a los workers configurados
   │     semantic → Worker RAG  (WORKER_RAG_URL)
   │     sql      → Worker SQL  (WORKER_SQL_URL)
   │     both     → ambos en secuencia
   │
   ├─ 3. Composición del borrador (respuestas + fuentes + notas)
   │
   ├─ 4. Fiscalización (si AUDITOR_URL configurada)
   │     → si ok=false y hay versión corregida, se entrega la corregida
   │
   └─ 5. Respuesta: {answer, sources, ruta, workers_usados, fiscalizacion, latency_ms}
```

## 3. Decisiones de diseño

| Decisión | Detalle | Razón |
|---|---|---|
| Router por LLM, no por reglas | DeepSeek clasifica la intención con criterios en el system prompt, salida JSON forzada (`response_format: json_object`) | Los criterios de delegación son semánticos ("cuántos" vs "qué dice el documento"); un LLM los generaliza mejor que regex |
| Temperatura 0 en el router | La ruta debe ser determinista | Una misma pregunta debe tomar siempre la misma ruta |
| Workers descubiertos por variables de entorno | `WORKER_RAG_URL`, `WORKER_SQL_URL`, `AUDITOR_URL` | Despliegue independiente por agente: cada servicio Cloud Run se redespliega sin tocar al orquestador; agregar un worker nuevo es solo setear otra variable |
| Degradación elegante | Si la ruta exige un worker no configurado, cae al worker RAG y agrega una nota explícita al usuario | La plataforma funciona aunque falten agentes; la nota preserva la transparencia |
| Fiscalización opcional pero prioritaria | Si `AUDITOR_URL` existe, toda respuesta pasa por el fiscalizador; si no, pasa directo | Permite desarrollo incremental sin romper el contrato |
| Fusión sin LLM adicional | Cuando solo responde un worker, su respuesta pasa tal cual; no hay llamada extra de "composición" | Evita latencia y costo innecesarios; los workers ya responden en formato citado |

## 4. Contrato con los workers

**Orquestador → Worker:** `POST {WORKER_URL}/ask` con `{"query": "..."}`

**Worker → Orquestador:**
```json
{
  "answer": "texto con citas",
  "sources": [{"fuente": "...", "seccion": "..."}]
}
```

**Orquestador → Fiscalizador:** `POST {AUDITOR_URL}/audit` con `{pregunta_original, borrador, fuentes_usadas}` → responde `{ok, issues, corrected}`.

## 5. Verificación local

Integración de los 4 agentes en local (puertos 8080–8083):

| Consulta de prueba | Ruta elegida | Workers usados | Resultado |
|---|---|---|---|
| "¿qué decisiones se tomarán en el comité del 7 de agosto?" | `semantic` | rag | Respuesta con citas; fiscalizador aprobó `ok=true` |
| "¿cuántos riesgos de exposición crítica o alta hay y cuál es el SPI?" | `both` | rag + sql | Fiscalizador detectó contradicción entre workers (`ok=false`, 3 issues) y el usuario recibió la versión corregida |
| "¿cuántos riesgos activos hay?" (sin worker SQL desplegado) | `sql` | rag (fallback) | Respuesta documental + nota: *"worker SQL aún no disponible"* |

- **Latencia:** ~8 s (ruta simple) / ~15 s (ruta `both` con fiscalización)
- **Costo por consulta:** 1 llamada DeepSeek del router + las de los workers + 1 del fiscalizador

## 6. Limitaciones conocidas

1. **Delegación secuencial:** en ruta `both` los workers se llaman uno tras otro; paralelizarlos (asyncio) reduciría la latencia casi a la mitad.
2. **Sin memoria conversacional:** cada consulta es independiente.
3. **Router sin few-shots:** el prompt usa solo criterios declarativos; un set de ejemplos mejoraría la precisión en preguntas ambiguas.
4. **`--max-instances=1` en el registro de interacciones:** SQLite sobre GCS FUSE no tolera escrituras concurrentes, así que el orquestador está limitado a una instancia. Con tráfico alto sería un cuello de botella (ver punto 7).

## 7. Registro de interacciones (paso 7 del roadmap)

Cada `POST /ask` termina registrando la interacción en la tabla `interactions` (SQLite nativo, sin SQLAlchemy): `id, timestamp, query, response, tokens, latency`. Persiste en `gs://pmo-ai-vectordb/interactions/interactions.db`, montado por Cloud Storage FUSE — mismo mecanismo que usa el worker RAG para Chroma.

Los `tokens` son la suma del `usage.total_tokens` de todas las llamadas LLM involucradas en la interacción: router + worker(s) delegado(s) + fiscalizador. Ese total se expone también en la respuesta de `/ask` (campo `tokens`).

`GET /stats` expone agregados (`total_interactions`, `total_tokens`, `avg_tokens`, `avg_latency_ms`, `min/max_latency_ms`, primera/última interacción) sin exponer `query`/`response` de filas individuales, ya que el endpoint es público sin auth. El registro nunca rompe la respuesta al usuario: si falla la escritura, solo se loggea un warning.

Detalle de diseño completo en `secret-zone/PLAN-trazabilidad.md`.

## 8. Cómo probarlo localmente

```bash
# 1. Levantar los workers (en terminales separadas)
uv run uvicorn src.worker_rag.serve:app --port 8080
uv run uvicorn src.worker_sql.serve:app --port 8082
uv run uvicorn src.auditor.serve:app --port 8083

# 2. Levantar el orquestador apuntando a ellos
WORKER_RAG_URL=http://localhost:8080 \
WORKER_SQL_URL=http://localhost:8082 \
AUDITOR_URL=http://localhost:8083 \
uv run uvicorn src.orchestrator.serve:app --port 8081

# 3. Consultar
curl -X POST localhost:8081/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "¿cuántos hitos están vencidos?"}'

# 4. Ver estadísticas de trazabilidad
curl localhost:8081/stats
```
