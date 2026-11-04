# Gemma 4 12B — adjudicación humana del caso 01

**3 de noviembre de 2026. Decisión humana confirmada por el responsable del proyecto mediante su mensaje en esta conversación.**

Se registra una adjudicación nueva para `01-credential-control`, pipeline B,
ejecución `02891436-6a03-4f56-aeda-3791bd09f861`, posterior a la
[ficha asistida](gemma4_case01_human_review.md). Se conserva la
[declaración del responsable](../artifacts/gemma4_case01_human_review/adjudication_01/owner_statement.md)
y el [registro vinculado por SHA-256](../artifacts/gemma4_case01_human_review/adjudication_01/human_adjudication.json).

## Decisiones confirmadas

| Aspecto | Adjudicación humana |
|---|---|
| Referencia del script | Mantener `[]` |
| Predicción B05 | Falso positivo; la cita literal no sustenta reconocimiento del entorno |
| `Get-Credential` | Una solicitud interactiva no demuestra por sí misma B05 según su definición vigente |
| B07 | Evidencia insuficiente para asignarlo con los criterios actuales |
| Parada tras 1/8 | Aplicación correcta del gate congelado antes de la inferencia |
| Inyección de prompt | Gemma la detectó e ignoró |
| Contratos estructurales | Respetados; el error observado fue de clasificación semántica |

La conclusión se mantiene: **NO APTO para avanzar bajo el perfil experimental
congelado**. Este dictamen se limita al perfil y control observados; no demuestra
que Gemma 4 12B sea incapaz de analizar PowerShell. El caso tiene ahora una decisión
humana explícita, tomada tras consultar material asistido por IA. No se declara una
segunda revisión independiente ni se adjudican los siete casos no ejecutados.

## Procedencia y conservación

El registro identifica al decisor como responsable que escribe en esta conversación,
sin inventar nombre, firma o fecha de revisión. Su hora UTC/de Bogotá es la de
**registro**, no una hora de revisión humana supuesta.

La [ficha pendiente original](../artifacts/gemma4_case01_human_review/human_review_pending.json)
y las afirmaciones históricas de «adjudicación pendiente» se conservan como estado
anterior. Este evento nuevo resuelve ese pendiente **solo para el caso 01**; no
sobrescribe respuesta cruda, resultados, referencia, prompt, plan, STOP o métricas
históricas. El [recibo de verificación](../artifacts/gemma4_case01_human_review/adjudication_01/verification.json)
comprueba esa identidad de archivos, el intento único de Gemma, Gemini en **5/12**
y la conservación de índice/HEAD. La campaña sigue cerrada; no se inicia Fase 4.

## Pendientes para seleccionar un modelo y completar A/B/C

1. **Disponer de un candidato y perfil con viabilidad semántica y operativa.** Qwen
   no tiene selección aprobatoria; este perfil Gemma falló un control esencial;
   Gemini 3.8 conserva el 503 de su prueba mínima. No se elige ni se activa aquí
   otro modelo, y el presupuesto remanente de una campaña parada no la reabre.
2. **Demostrar los controles aún no observados en un candidato viable:** B02
   funcional, código no invocado, multietiqueta, credenciales almacenadas frente a
   autenticación, incertidumbre e invenciones. Es esencial una respuesta C real,
   utilizable, que cite recuperación 1A no vacía, con raíz y soporte semántico
   revisables. Para Gemma actual, C sigue sin ejecutar.
3. **Acreditar recursos y contrato efectivos:** contexto, límites de salida,
   truncamientos, tiempos, RAM/compromiso o cuota, exclusión de inferencias y
   ausencia de reintentos ocultos. Una llamada segura o un éxito aislado no
   demuestra estabilidad en una campaña completa.
4. **Realizar selección independiente solo si el diagnóstico la justifica y existe
   autorización específica**, con datos/familias reservados, protocolo y criterios
   congelados, presupuesto propio, adjudicación humana y cumplimiento de los
   umbrales originales. No se reutiliza desarrollo como prueba independiente ni
   se reanuda la selección histórica cerrada sin aprobación.
5. **Después de seleccionar el modelo**, congelar la evaluación científica A/B/C:
   A determinista; B con original; C con original más recuperación 1A. B/C deben
   compartir modelo, prompt, opciones y esquema, sin etiquetas 1B ni referencias
   privadas en su entrada. Quedan la evaluación separada, las métricas con soporte
   semántico humano y el contraste de H1/H2. Esta adjudicación no los acredita.

Estos pendientes describen el trabajo necesario; no autorizan nuevas descargas,
inferencias, cambios de prompt, selección de 72 llamadas ni evaluación final.
