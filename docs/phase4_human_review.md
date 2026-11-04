# Fase 4 — revisión personal prospectiva

## Antes de ver respuestas B/C

Revisar las [16 fichas propuestas](phase4_references_proposed.md) y el [audit de independencia](phase4_independence_review.md). Para cada ID comprobar texto/hash, inclusiones y exclusiones B01–B07, alcance completo/parcial/indeterminado, evidencias localizadas, invocación frente a almacenamiento, recuperación 1A y seguridad. Compartir un cmdlet con el desarrollo no basta para rechazar independencia; compartir su programa base con meros cambios de nombres/literales sí obliga a sustituir o agrupar el caso antes de congelar.

F4-15 no tiene conjunto determinable; F4-16 solo tiene B05 conocida como mínimo. No convertir `null` en `[]`. No usar etiquetas de 1B ni predicciones B/C para corregir referencias. Si la revisión requiere cambios, registrar una nueva versión candidata antes de generar nada.

Copiar `reference_review.template.json` a un archivo nuevo, completar nombre real, fecha ISO con zona horaria y notas, y aprobar cada caso solo después de revisarlo. Las aprobaciones de referencias, independencia y seguridad deben ser expresas. No atribuir la revisión a una segunda persona que no haya intervenido. La revisión liga el hash candidato, el hash del texto y el de la referencia de cada ID.

La propuesta se sella posteriormente con `seal --personal-review ...`; este comando **no ejecuta inferencias**. Una autorización de ejecución futura, distinta y ligada al congelado, es necesaria para `run`. El presupuesto no se transfiere del diagnóstico agotado de ocho intentos ni de Gemini.

## Después de una futura campaña

Conservar la respuesta cruda y su estado incluso si es JSON inválido, cita inventada, salida limitada o clasificación incorrecta. No editar el crudo, corregir etiquetas publicadas ni pedir al modelo una reparación. Revisar B y C como respuestas separadas vinculadas a su hash completo, ID y modo. El orden de revisión puede alternarse, pero no se afirmará cegamiento o independencia del anotador si no ocurrió; las fuentes recuperadas suelen revelar C.

Crear un inventario de **afirmaciones factuales atómicas** de todos los campos: comportamientos, explicaciones, reconstrucción, atribución, fundamentos de riesgo e incertidumbre. No limitarse a `behaviors`, ignorando afirmaciones en `limitations` o `notes`. Cada afirmación debe tener ID, proposición, cita literal del crudo, fuentes utilizadas, razonamiento y valoración estricta. Las repeticiones de la misma proposición dentro de una respuesta se cuentan una sola vez; se anotan sus repeticiones como observación de verbosidad, sin convertir paráfrasis redundantes en hechos nuevos.

Separar una afirmación sobre el programa de una postura epistémica o texto procedimental sin contenido factual sobre él. No inventar afirmaciones para llenar un inventario vacío. El inventario completo vacío, ilegible o no adjudicable no obtiene una tasa favorable de errores cero: se reporta no evaluable para H2 y su cobertura queda visible.

Categorías estrictas:

1. `individual`: cita realmente emitida y verificable suficiente para la afirmación.
2. `contextual_cited`: varias citas emitidas relacionadas y/o recuperación del sistema efectivamente disponible en C sustentan juntas la afirmación.
3. `insufficient`: evidencia literal o fuentes mencionadas no alcanzan para sostener la conclusión bajo la política estricta.
4. `contradicted`: la afirmación contradice código, activación, taxonomía, contenido recuperado o procedencia comprobables.
5. `unassessable`: no puede adjudicarse con los materiales disponibles; no se trata como apoyada.

Como evaluación secundaria, `permissive_context_support` registra si contexto no citado del original resolvería la insuficiencia. No usarlo para corregir retrospectivamente el resultado estricto. Una reconstrucción del modelo no es recuperación del motor; solo puede corroborarse contra el original y las fuentes verificadas realmente disponibles. La literalidad automática no decide ninguna categoría semántica.

Registrar también número de reconstrucciones inventadas/alteradas, referencias de fuente inexistentes, evaluación de riesgo/ incertidumbre y razones de indeterminación. Para una afirmación de ausencia o benignidad, revisar alcance y desconocidos; no sustituir “no vi evidencia” por “demostré que no ocurre”. El éxito efectivo de llamadas de red, tareas o credenciales nunca fue comprobado mediante ejecución.

Formato de revisión por salida (plantilla genérica, **sin adjudicación real**):

```json
{
  "unit": "F4-XX",
  "mode": "B",
  "result_sha256": null,
  "reviewer_type": "human_personal",
  "reviewer": "",
  "reviewed_at": "",
  "human_confirmed": false,
  "inventory_complete": false,
  "invented_reconstructions": 0,
  "altered_reconstructions": 0,
  "risk_uncertainty_notes": "",
  "claims": [
    {
      "claim_id": "CL01",
      "proposition": "",
      "quote": "",
      "strict_support": "unassessable",
      "permissive_context_support": false,
      "source_ids": [],
      "rationale": ""
    }
  ]
}
```

El evaluador exige nombre, confirmación personal, fecha posterior a la salida, hash íntegro, ID/modo correctos, inventario completo y citas existentes en el crudo. Esa validación formal no demuestra por sí sola que la adjudicación humana sea correcta. Si hay una segunda revisión independiente real, conservar ambos eventos y los desacuerdos; no fabricar acuerdo entre anotadores o kappa.

La [rúbrica y protocolo](phase4_protocol_proposed.md) se revisan antes de congelar. Las ocho adjudicaciones del diagnóstico Qwen14 siguen pendientes en sus propios artefactos de desarrollo; no se rellenan con estas futuras 32 revisiones ni se convierten en aceptación implícita.
