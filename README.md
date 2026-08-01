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

## Ambiente

- Python 3.12, gestionado con `uv`
- Instalar dependencias: `uv sync` (o `uv pip install -r <agente>/requirements.txt`)
- Ejecutar código local: siempre con `uv run`, ej. `uv run <agente>/agent.py`

## Convenciones

- Cada agente tiene su propio `requirements.txt` y `.env` (con `DEEPSEEK_API_KEY`; nunca commitear, `.env` está en `.gitignore`)
- Usamos DeepSeek como proveedor de LLM (no OpenAI)
- Los prompts de los agentes están en español
