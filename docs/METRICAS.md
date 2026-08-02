# Métricas del sistema: latencia y costo

Datos medidos sobre el despliegue en producción (Cloud Run, región `southamerica-west1`), a partir de las interacciones reales registradas en `.interactions/interactions.db`.

## Latencia

| Ruta | Latencia |
|---|---|
| Consulta simple (una sola ruta: `semantic` o `sql`) | ~8s |
| Consulta mixta (`both`: RAG + SQL + fiscalización) | ~15–30s |
| Worker RAG solo (instancia warm) | ~2,5–3,5s |

**Datos reales medidos** (3 interacciones registradas en la base de trazabilidad):

- Latencias individuales: 6.026 ms, 11.632 ms, 5.615 ms
- Promedio: 7.757,7 ms
- Mínimo: 5.615 ms
- Máximo: 11.632 ms

La ruta `both` es la más lenta porque hoy el orquestador llama a los workers de forma **secuencial** (ver mejora pendiente de paralelización en `MEJORAS_PENDIENTES.md`).

No existe todavía una suite formal de benchmarks (`evals/`, `tests/` de performance); estos números provienen de la documentación de cada componente (`AGENTE.md`) y de la tabla de trazabilidad real.

## Costo

**Modelos usados:**
- LLM: `deepseek-chat` (DeepSeek, API compatible OpenAI SDK) — usado en router, worker RAG, worker SQL y fiscalizador.
- Embeddings: `text-embedding-004` (Vertex AI / Google), 768 dimensiones.

**Estimación: menos de US$1 por 1.000 consultas**

| Componente | Costo aprox. por 1.000 consultas |
|---|---|
| Embeddings (Vertex AI) | ~US$0,01 |
| DeepSeek (LLM) | ~US$0,10 – 0,20 |
| Cloud Run (cómputo) | ~US$0,50 |

**Consumo real de tokens** (capturado en la tabla `interactions`):

- Tokens por interacción: 1.247, 4.154, 2.491
- Promedio: 2.630,7 tokens por consulta

Cada consulta dispara entre 2 y 4 llamadas LLM (router + worker(s) + fiscalizador), lo que explica la variabilidad en tokens consumidos según la ruta elegida.

> Nota: este es un cálculo estimado a partir de los precios públicos de DeepSeek y Vertex AI, no una hoja de costos formal con facturación real de GCP.
