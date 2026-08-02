# Mejoras pendientes

Trabajo futuro identificado durante el desarrollo de PMO-AI, pendiente de implementación.

## 1. Paralelizar llamadas a workers en la ruta `both`

Hoy, cuando el orquestador decide que una consulta requiere tanto búsqueda semántica como SQL (ruta `both`), llama a los workers **de forma secuencial**, lo que casi duplica la latencia total (~15–30s vs ~8s de una consulta simple).

**Propuesta:** ejecutar las llamadas a worker RAG y worker SQL en paralelo (async/concurrent), y componer la respuesta final una vez que ambas retornan. Debería acercar el tiempo de respuesta de la ruta mixta al de una consulta simple.

## 2. Evaluación formal del retriever (precisión@k)

Actualmente no existe una suite de evaluación cuantitativa para el worker RAG. La calidad de la búsqueda semántica (KNN k=5 sobre ChromaDB) se valida de forma cualitativa, sin métricas objetivas.

**Propuesta:** construir un set de referencia de ~10 consultas con resultados esperados conocidos, medir precisión@k, y usar esos resultados para justificar ajustes de `k`, estrategia de chunking, o comparar contra hybrid search (semántico + keyword).

## 3. Endurecer comunicación interna (IAM entre servicios)

Hoy los 4 servicios (orquestador, worker RAG, worker SQL, fiscalizador) están desplegados como endpoints públicos de Cloud Run, sin restricción de invocación. Cualquiera con la URL puede llamar directamente a un worker o al fiscalizador, saltándose al orquestador.

**Propuesta:** configurar IAM en Cloud Run para que worker RAG, worker SQL y fiscalizador solo acepten invocaciones autenticadas desde la service account del orquestador, cerrando el acceso público directo a los componentes internos.

---

## Otras limitaciones conocidas (no priorizadas)

- **Capa determinista de PII:** el fiscalizador valida PII solo vía LLM; falta una capa de reglas (regex RUT, tarjetas, emails) como complemento determinista.
- **Worker RAG sobre GCS FUSE:** Chroma no tolera bien escrituras concurrentes; la actualización del índice es manual y no hay memoria conversacional.
- **Worker SQL:** datos estáticos (requiere redeploy para actualizar), esquema pequeño, solo dialecto SQLite.
- **Fiscalizador:** no verifica veracidad factual contra fuentes (solo coherencia y presencia de citas); es fail-open si el servicio cae.
- **Orquestador:** limitado a `--max-instances=1` por el cuello de botella de SQLite sobre FUSE; el router no usa few-shots.
