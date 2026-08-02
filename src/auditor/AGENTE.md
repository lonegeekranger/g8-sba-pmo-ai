# Agente Fiscalizador — PMO-AI

**Curso:** Simulación Basada en Agentes — Programa de Inteligencia Artificial, UAI
**Fecha:** Agosto 2026
**Estado:** Construido y verificado localmente — pendiente de despliegue
**Rol en la plataforma:** Agente 4 de 4 (ver `masterplan.md`) — valida toda respuesta antes de que llegue al usuario (paso 5 del roadmap)

---

## 1. Qué es este agente

El fiscalizador es el **control de calidad de la plataforma**. Ninguna respuesta del orquestador llega al usuario sin pasar por él. Recibe el borrador de respuesta junto con la pregunta original y las fuentes usadas, y aplica las tres reglas de validación exigidas por el roadmap:

1. **Citas:** toda afirmación relevante debe citar su origen `(Fuente: ..., Sección: ...)` o referencia a datos tabulares/SQL
2. **PII:** no debe exponer datos sensibles ni personales (RUT, tarjetas, personas reales identificables)
3. **Relevancia:** la respuesta debe contestar la pregunta original, no otra cosa

Su salida sigue el contrato fijado por el roadmap: `{ok, issues, corrected}`.

## 2. Flujo

```
Orquestador → POST /audit
  {pregunta_original, borrador, fuentes_usadas}
   │
   ├─ DeepSeek (temperatura 0, salida JSON) evalúa las 3 reglas
   │
   └─ Respuesta:
      ok=true               → el orquestador entrega el borrador tal cual
      ok=false + corrected  → el orquestador entrega la versión corregida
      ok=false sin corrected → el orquestador entrega el borrador
                               (la plataforma nunca se queda sin respuesta)
```

## 3. Decisiones de diseño

| Decisión | Detalle | Razón |
|---|---|---|
| Corrección restrictiva | El prompt prohíbe inventar datos: la corrección solo puede reformular, eliminar lo no citado o agregar aclaraciones | Un fiscalizador que "arregla" inventando datos sería peor que el problema |
| Temperatura 0 + JSON forzado | Veredicto determinista y parseable | El orquestador consume el resultado programáticamente; no puede haber ambigüedad de formato |
| El fiscalizador no conoce a los workers | Solo ve pregunta, borrador y fuentes | Acoplamiento cero: sirve para cualquier combinación de workers presentes y futuros |
| Fallo abierto (fail-open) en el orquestador | Si el fiscalizador no está configurado o falla, la respuesta pasa | Disponibilidad prioritaria en desarrollo; en producción se evalúa fail-closed (bloquear si no fiscaliza) |

## 4. Verificación local: caso real detectado

En la integración de los 4 agentes, la consulta *"¿cuántos riesgos de exposición crítica o alta hay y cuál es el SPI?"* (ruta `both`) produjo un borrador donde el Worker RAG decía que el documento no especificaba niveles de exposición mientras el Worker SQL afirmaba que había 4. El fiscalizador respondió:

```json
{
  "ok": false,
  "issues": [
    "La respuesta contiene dos afirmaciones contradictorias sobre el número de riesgos...",
    "La afirmación de que hay 4 riesgos... no se presenta de manera clara y consistente",
    "Debe aclararse que la cifra proviene de los datos tabulares, no del documento"
  ],
  "corrected": "Según los datos tabulares del proyecto, hay 4 riesgos de exposición crítica o alta (Fuente: datos tabulares del proyecto, Consulta SQL). El documento en su Sección 5 no especifica niveles de exposición, por lo que la cifra de 4 proviene de la base de datos..."
}
```

El usuario recibió la versión corregida, coherente y con la procedencia de cada cifra aclarada. En consultas sin problemas (ruta documental simple), el fiscalizador aprobó `ok=true` sin modificar nada.

## 5. Limitaciones conocidas

1. **Validación por LLM, no por reglas deterministas:** la detección de PII se apoya en el criterio del modelo; una capa adicional con regex (RUT, tarjetas, emails) la haría más robusta y auditable.
2. **No verifica la veracidad factual contra las fuentes:** valida que *haya* citas y que el texto sea coherente, pero no recupera los chunks originales para comprobar que la cita dice lo que la respuesta afirma (eso sería un verificador de groundedness, mejora futura).
3. **Costo y latencia:** agrega una llamada DeepSeek por consulta (~2-3 s). Aceptable para el caso de uso; en alto volumen se podría fiscalizar por muestreo.
4. **Fail-open:** hoy, si el fiscalizador está caído, la respuesta pasa igual. Para producción se recomienda fail-closed con timeout corto y alerta.

## 6. Cómo probarlo localmente

```bash
uv run uvicorn src.auditor.serve:app --port 8083

curl -X POST localhost:8083/audit \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta_original": "¿cuál es el SPI del proyecto?",
    "borrador": "El SPI es 0,89 según las métricas del proyecto.",
    "fuentes_usadas": [{"fuente": "PMO-FER-2025-014.md", "seccion": "6. Métricas"}]
  }'
```
