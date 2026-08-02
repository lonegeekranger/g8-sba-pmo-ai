# PMO-AI — Agente de Inteligencia Operacional para la Gestión de Proyectos TI

Tarea final del curso **Simulación Basada en Agentes**, Programa de Inteligencia Artificial, Universidad Adolfo Ibáñez.
Profesor: Ahmad Armoush

**Integrantes:** William Añez · Carlos Vizcaya · Germán Pache

## Problema

Las oficinas de proyectos TI (PMO) manejan grandes volúmenes de documentación dispersa en múltiples sistemas y formatos, lo que obliga a los project managers a invertir horas buscando datos para decisiones operativas.

## Solución

PMO-AI es un agente que permite consultar en lenguaje natural:

- Estado del portafolio de proyectos
- Alertas de riesgo
- Hitos vencidos
- Métricas de desempeño

Toda respuesta es **trazable a los documentos fuente**, con citas explícitas del nombre del proyecto y la sección de origen.

## Justificación

- **Complejidad balanceada:** documentos estructurados y preguntas acotadas que permiten profundidad técnica dentro de plazos razonables.
- **Trazabilidad:** cada respuesta incluye citas explícitas del nombre del proyecto y sección de origen.
- **Escalabilidad:** permite agregar fácilmente más proyectos o integrar workers especializados (alertas, presupuestos).

## Estructura del repositorio

```
data/           # Documentos fuente del portafolio de proyectos
docs/           # Documentación del proyecto (propuesta, roadmap)
sample-agents/  # Agentes de referencia en Python (LangChain + OpenAI)
```

## Uso fácil (CLI)

El proyecto está desplegado en GCP, por lo que **no hace falta levantar nada local**: el CLI conversa directamente con el orquestador remoto.

```bash
uv sync          # solo la primera vez, para instalar dependencias
uv run cli.py
```

Se abre un chat interactivo (`pmo-ai>`). Escribe la pregunta, presiona Enter y el agente responde con citas a los documentos fuente. `salir` o Ctrl+C para terminar.

Ejemplos de preguntas para probar:

```
¿cuál es el estado del portafolio?
¿cuántos hitos están vencidos y qué riesgo los causa?
¿cuántos riesgos hay por nivel de exposición?
¿cuáles son las métricas SPI y CPI del proyecto?
```

Las consultas simples tardan ~8 s; las que combinan búsqueda documental y SQL con fiscalización pueden tardar ~30 s.

> El endpoint por defecto es el orquestador en Cloud Run. Para apuntar a otra URL: `PMO_AI_URL=http://localhost:8080 uv run cli.py`

### Agregar documentos al agente

Para que el agente conozca nuevos proyectos, agrega su `.md` a `data/` y corre:

```bash
uv run cli.py cargar                      # indexa todo lo que hay en data/
uv run cli.py cargar ~/otros/proyecto.md  # además copia archivos externos a data/
```

El comando chunkea los documentos por secciones, genera los embeddings (Vertex AI), actualiza el índice Chroma local y lo sincroniza al bucket GCS que monta el worker RAG. Es idempotente: re-cargar un documento existente lo actualiza sin duplicar.

**Prerrequisitos** (solo para quien administra el índice, no para el profesor): Google Cloud SDK instalado, credenciales activas (`gcloud auth application-default login`) y permisos sobre el bucket `pmo-ai-vectordb`.

**Notas:**
- Si el agente no ve los documentos nuevos al consultar, fuerza una nueva revisión del worker: `gcloud run services update pmo-ai-worker-rag --region southamerica-west1`
- Los documentos nuevos solo alimentan la búsqueda semántica (RAG). Las consultas SQL operan sobre las 4 tablas extraídas del documento original; extenderlas requiere cargar tablas nuevas.

## Ambiente

- Python 3.12, gestionado con `uv`
- Instalar dependencias: `uv sync` (o `uv pip install -r <agente>/requirements.txt`)
- Ejecutar código local: siempre con `uv run`, ej. `uv run <agente>/agent.py`

## Convenciones

- Cada agente tiene su propio `requirements.txt` y `.env` (con `DEEPSEEK_API_KEY`; nunca commitear, `.env` está en `.gitignore`)
- Usamos DeepSeek como proveedor de LLM (no OpenAI)
- Los prompts de los agentes están en español
