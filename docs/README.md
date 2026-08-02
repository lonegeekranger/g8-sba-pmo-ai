# Documentación del proyecto

## `G8 SBA PMO AI.pdf`

Documento oficial de la tarea del curso Simulación Basada en Agentes (Programa de Inteligencia Artificial, UAI). Define el enunciado del proyecto: construir un agente conversacional para una PMO que responda preguntas sobre el estado de un proyecto a partir de un documento de negocio, con los requisitos, entregables y criterios de evaluación del trabajo grupal.

## `Roadmap_Agente_Produccion_UAI.pdf`

Material del taller "10 pasos para llevar un agente a producción" (UAI). Es la guía metodológica que seguimos para estructurar el desarrollo: desde el RAG mínimo viable hasta la arquitectura multi-agente, pasando por orquestación, workers especializados, fiscalización, observabilidad y despliegue. Cada decisión de arquitectura del proyecto referencia el paso del roadmap que la origina.

## `IMPLEMENTACION.md`

Documento técnico consolidado del proyecto PMO-AI. Describe la metodología de trabajo incremental (documento → RAG → multi-agente), la arquitectura de 4 agentes (orquestador, worker RAG, worker SQL, fiscalizador), la infraestructura en GCP (Cloud Run, Cloud Storage FUSE, Secret Manager), las decisiones de diseño relevantes (DeepSeek como LLM, chunking por secciones, router por LLM, degradación elegante) y los resultados de validación contra el endpoint público. Es el documento de referencia para entender cómo está construido el sistema.

## `Ferretodo_Pet_MiroFish_v2.pdf`

Documento semilla (SEED) que usamos como input para el análisis con MiroFish en clases pasadas del curso. Contiene el contexto de negocio de Ferretodo a partir del cual la simulación multi-agente de MiroFish generó los insumos que luego consolidamos en el documento de proyecto. Es el origen de la cadena documental: seed → análisis MiroFish → documento PMO sintético.

## `data/PMO-FER-2025-014_motor_recomendacion_proyecto_completo.md`

Documento de negocio sintético que sirve como fuente de datos para los agentes. Es el resultado de la cadena de investigación iniciada en clases pasadas del curso: partimos del seed `Ferretodo_Pet_MiroFish_v2.pdf`, lo procesamos con [MiroFish](https://github.com/666ghj/MiroFish) (simulación multi-agente que explora y enriquece un escenario de negocio) y a partir de ese análisis construimos un reporte PMO realista y denso: ficha del proyecto PMO-FER-2025-014 (Ferretodo Chile), hitos con atrasos, riesgos activos y materializados, métricas (SPI/CPI), presupuesto, equipo, dependencias externas y decisiones pendientes de comité. Su densidad es deliberada: permite formular preguntas interesantes al sistema (hitos vencidos, riesgos críticos, desvíos presupuestarios) y validar tanto la ruta semántica como la ruta SQL.
