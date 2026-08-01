# Proyecto PMO-FER-2025-014 — Motor de Recomendación de Proyecto Completo

**Empresa:** Ferretodo Chile (Grupo Andesmall)
**Estado PMO:** En ejecución — Semáforo AMARILLO (tendencia roja en integración ObraDirecta)
**Fecha de corte del presente reporte:** 31 de julio de 2026
**Clasificación:** Interno — Uso PMO y Comité de Proyecto

---

## 1. Ficha del proyecto

| Campo | Detalle |
|---|---|
| Código PMO | PMO-FER-2025-014 |
| Nombre | Motor de Recomendación de Proyecto Completo ("Asistente de Obra") |
| Sponsor ejecutivo | Andrea Solís, Gerente Comercial Hogar Central |
| Product Owner | Marcela Fuentes, Gerencia Digital Transversal |
| Project Manager | Ignacio Herrera, PMO Corporativa |
| Líder técnico | Sebastián Rojas, Arquitectura de Datos e IA |
| Fecha de inicio | 5 de enero de 2026 |
| Go-live objetivo (baseline) | 7 de septiembre de 2026 (app + e-commerce + kioscos ObraDirecta) |
| Go-live proyectado actual | 21 de septiembre de 2026 (deslizamiento de 2 semanas) |
| Presupuesto aprobado | CLP $1.840.000.000 |
| Presupuesto ejecutado al corte | CLP $1.276.400.000 (69,3%) |
| Metodología | Híbrida: fases de levantamiento en cascada, construcción en sprints de 2 semanas |
| Criticidad | Estratégica — vinculada a meta de marca propia (28% → 35% participación en 2 años) |

## 2. Objetivo y alcance

Construir un motor de recomendación que, a partir de un ítem buscado o comprado, arme y sugiera el listado completo de materiales para una obra o remodelación (ej.: si el cliente compra cemento, sugiere fierro, arena, aditivo y herramienta de mezcla).

**Canales en alcance:**

1. App Ferretodo (iOS/Android)
2. Sitio e-commerce
3. Kioscos de autoconsulta del formato ObraDirecta (74 locales)

**Fuentes de datos en alcance:**

- Historial de compra vinculado a tarjeta ConstruCard (3,2 millones de tarjetas activas)
- Perfil de obra de los miembros de la Red de Maestros (1.040.000 miembros activos)
- Maestro de productos: 48.500 SKU, incluidas las 24 marcas propias (Nortex, Vantia, Duralt, Prakko y otras)
- Catálogo técnico de recetas de obra (2.300 recetas validadas por el área de Categorías)

**Fuera de alcance (explícito):** integración con el sistema de arriendo de herramientas (en evaluación por la entrada de ToolShare Brasil), recomendación en caja/POS físico, y módulo de precios dinámicos.

## 3. Arquitectura técnica

- **Pipeline de datos:** ingesta batch nocturna desde el ERP y el CRM de ConstruCard hacia el lakehouse (GCP BigQuery); features de cliente actualizadas a las 04:00.
- **Modelo de recomendación:** ensamble de dos etapas — candidatos por co-compra y recetas de obra (reglas + collaborative filtering), re-ranking con modelo gradient boosting que pondera relevancia técnica, margen y disponibilidad en tienda.
- **Capa de servicio:** API en Cloud Run, SLA de respuesta p95 < 800 ms, caché en Memorystore (Redis) para las 5.000 consultas de proyecto más frecuentes.
- **Kioscos ObraDirecta:** cliente embebido con modo offline degradado (catálogo local de 24 horas).
- **Gobernanza de datos personales:** dataset de ConstruCard anonimizado con seudonimización reversible solo en el ambiente enmascarado; acceso bajo rol `data-recommender` auditado mensualmente por Cumplimiento.

## 4. Hitos

| # | Hito | Fecha baseline | Fecha real / proyectada | Estado |
|---|---|---|---|---|
| H1 | Charter aprobado y equipo constituído | 30-ene-2026 | 30-ene-2026 | Completado |
| H2 | Levantamiento de recetas de obra y reglas de negocio | 13-mar-2026 | 27-mar-2026 | Completado (2 semanas atraso) |
| H3 | Pipeline de datos ConstruCard en producción | 17-abr-2026 | 08-may-2026 | Completado (3 semanas atraso) |
| H4 | Modelo MVP con precisión@5 ≥ 0,62 en set de validación | 29-may-2026 | 05-jun-2026 | Completado (precisión@5 = 0,64) |
| H5 | Integración app y e-commerce en ambiente QA | 10-jul-2026 | 24-jul-2026 | Completado (2 semanas atraso) |
| H6 | Integración kioscos ObraDirecta (piloto 6 locales) | 07-ago-2026 | 28-ago-2026 (proyectada) | **VENCIDO** — bloqueado por firmware de kioscos |
| H7 | Pruebas de carga y pentesting | 21-ago-2026 | 04-sep-2026 (proyectada) | En riesgo |
| H8 | Aprobación de Cumplimiento (tratamiento datos ConstruCard) | 28-ago-2026 | 11-sep-2026 (proyectada) | En riesgo |
| H9 | Go-live canal digital (app + e-commerce) | 07-sep-2026 | 21-sep-2026 (proyectada) | Deslizado |
| H10 | Go-live kioscos ObraDirecta (74 locales) | 07-sep-2026 | 05-oct-2026 (proyectada) | Deslizado |

**Resumen:** 5 hitos completados, 4 con atraso acumulado. El camino crítico actual pasa por H6 (firmware de kioscos) y H8 (aprobación de Cumplimiento).

## 5. Riesgos activos

| ID | Riesgo | Prob. | Impacto | Exposición | Dueño | Plan de respuesta |
|---|---|---|---|---|---|---|
| R-01 | Firmware de kioscos ObraDirecta (v3.2) no soporta el cliente embebido; actualización requiere visita técnica a 74 locales | Alta | Alto | Crítico | S. Rojas | Escalar con proveedor NexKiosk; evaluar despliegue OTA parcial; decisión en comité 07-ago-2026 |
| R-02 | Cumplimiento objeta el uso de historial ConstruCard para perfiles de menores de edad detectados en cuentas familiares | Media | Alto | Alto | I. Herrera | Regla de exclusión por segmento etario; dictamen esperado 14-ago-2026 |
| R-03 | Conflicto de función objetivo: ponderación de margen (marca propia) vs. relevancia técnica sin definición formal | Alta | Medio | Alto | A. Solís / M. Fuentes | Comité de 07-ago-2026 debe fijar factor de ponderación por canal |
| R-04 | Desplazamiento de marcas líderes gatilla retiro de inversión publicitaria de 3 proveedores con posiciones de retail media comprometidas | Media | Medio | Medio | C. Reyes | Reservar slots fijos de retail media fuera del ranking algorítmico |
| R-05 | Latencia p95 supera SLA en horario peak de kioscos (sábado 10:00–14:00) | Media | Medio | Medio | S. Rojas | Pre-calentar caché con recetas top por zona geográfica |
| R-06 | Dependencia del equipo de Categorías para mantener recetas: solo 2 personas con conocimiento del modelo de recetas | Media | Alto | Alto | M. Fuentes | Documentación y plan de transferencia a tercer analista en septiembre |
| R-07 | Entrada de ToolShare Brasil (8 locales, octubre 2026) presiona a adelantar go-live sacrificando pruebas | Baja | Alto | Medio | I. Herrera | Mantener gates de calidad; escenario de go-live anticipado requiere aprobación de sponsor |

**Riesgos materializados (ahora problemas):**

- P-01 (ex R-08): La ponderación de marca propia 2x impuesta por la Gerencia Comercial el 24-jul-2026 degradó la precisión@5 de 0,64 a 0,55 en el set de validación ObraDirecta. Se abrió desviación de alcance DEV-03.
- P-02: El 65% del presupuesto de descuentos e inversión de la Red de Maestros del segundo semestre ya está comprometido, limitando incentivos de adopción del motor en ese canal.

## 6. Métricas de desempeño del proyecto

| Métrica | Valor al corte | Comentario |
|---|---|---|
| SPI (Schedule Performance Index) | 0,89 | Tendencia a la baja por H6 |
| CPI (Cost Performance Index) | 1,02 | Aún en rango; despliegue OTA de kioscos agregaría ~CLP $38 MM |
| Defectos abiertos (críticos / mayores / menores) | 3 / 17 / 42 | Los 3 críticos son del cliente de kiosco |
| Cobertura de pruebas automatizadas | 78% | Meta de go-live: 85% |
| Precisión@5 modelo (validación digital) | 0,64 | Con ponderación técnica pura |
| Precisión@5 modelo (validación ObraDirecta, ponderación 2x marca propia) | 0,55 | Bajo umbral de aceptación de 0,60 — ver P-01 |
| Latencia p95 API (pruebas de carga preliminar) | 690 ms | Dentro de SLA 800 ms; pendiente prueba full con 74 kioscos |
| Horas-hombre consumidas | 6.940 de 9.200 planificadas | 75,4% |
| Satisfacción del sponsor (encuesta mensual) | 3,1 / 5 | Cayó desde 4,2 en mayo por el deslizamiento del go-live |

## 7. Presupuesto

| Partida | Aprobado (CLP MM) | Ejecutado (CLP MM) | % |
|---|---|---|---|
| Equipo interno (horas) | 620 | 468 | 75,5% |
| Consultora de datos (DataAndes SpA) | 480 | 351 | 73,1% |
| Infraestructura GCP (18 meses) | 210 | 122 | 58,1% |
| Licencias y herramientas | 130 | 98 | 75,4% |
| Hardware kioscos (adaptadores, pruebas) | 180 | 96 | 53,3% |
| Contingencia | 220 | 141,4 | 64,3% |
| **Total** | **1.840** | **1.276,4** | **69,3%** |

**Alerta financiera:** la contingencia está consumida en 64% con el proyecto al 75% de horas; un despliegue OTA de firmware o una extensión del contrato de DataAndes requeriría solicitar refuerzo de CLP $60–90 MM al Comité de Inversión.

## 8. Equipo y proveedores

- **PM:** Ignacio Herrera (PMO Corporativa, dedicación 75%)
- **Product Owner:** Marcela Fuentes (Gerencia Digital, 50%)
- **Líder técnico:** Sebastián Rojas + 2 ingenieros de datos internos
- **Consultora:** DataAndes SpA — 3 data scientists, contrato hasta 30-sep-2026 (extensible 2 meses)
- **Proveedor kioscos:** NexKiosk Chile (hardware y firmware, SLA de soporte 48 h)
- **QA:** 2 testers internos + 1 automatizador de la consultora
- **Cumplimiento/DPO:** Paula Ugarte (aprobaciones de tratamiento de datos personales)

## 9. Dependencias externas

1. **Congelamiento de precios** (2.000+ SKU hasta fin de año): el motor no puede recomendar sustitutos cuyo precio de referencia haya subido — regla implementada en el re-ranking, validada por Comunicaciones.
2. **Retail media:** Constanza Reyes comprometió 3 posiciones destacadas a proveedores de marcas líderes para primavera-verano; el diseño de slots fijos debe estar cerrado antes del 15-ago-2026.
3. **Red de Maestros:** Rodrigo Aliaga exige que en el canal ObraDirecta los ítems visibles para el cliente final (pintura de terminación, grifería) excluyan ponderación de marca propia; pendiente de decisión en comité.
4. **Migración del ERP (proyecto PMO-FER-2025-007):** ventana de congelamiento de interfaces 12–25 de septiembre; si el go-live digital se confirma para el 21-sep, se requiere exención formal.

## 10. Decisiones pendientes (comité 07-ago-2026)

1. Factor de ponderación de marca propia por canal: 2x transversal (propuesta A. Solís) vs. 1x en ObraDirecta / 1,5x en Hogar Central (propuesta R. Aliaga y M. Fuentes).
2. Escenario frente a kioscos: OTA parcial (costo adicional CLP $38 MM) vs. go-live digital primero y kioscos en octubre.
3. Aceptación o reversa de la desviación DEV-03 (precisión@5 bajo umbral en ObraDirecta).
4. Solicitud de refuerzo de contingencia al Comité de Inversión.

## 11. Bitácora de cambios de alcance

| ID | Fecha | Cambio | Impacto | Estado |
|---|---|---|---|---|
| CR-01 | 20-feb-2026 | Se agrega modo offline degradado para kioscos | +CLP $45 MM, +2 semanas | Aprobado |
| CR-02 | 10-abr-2026 | Se excluye integración POS físico del alcance | −CLP $60 MM | Aprobado |
| DEV-03 | 24-jul-2026 | Ponderación marca propia 2x transversal impuesta por sponsor | Precisión@5 ObraDirecta cae a 0,55 | En disputa — ver comité 07-ago |

## 12. Próximos hitos de reporte

- Comité de proyecto: 07-ago-2026 (decisiones D1–D4)
- Dictamen Cumplimiento (R-02): 14-ago-2026
- Reporte de estado PMO mensual: 31-ago-2026
- Gate de go-live digital: 14-sep-2026 (proyectado)
