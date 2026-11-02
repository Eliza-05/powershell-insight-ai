# Piloto v2: protocolo vigente de modelo unico (r2)

**Estado vigente: dataset y criterios r1 aprobados globalmente y congelados; descarga e inferencias autorizadas por la instruccion de cierre. Se evalua exclusivamente `qwen3.5:4b-q4_K_M`; la calidad aun depende del resultado. La Fase 2 no comienza.**

Procedencia: [aprobacion global](../experiments/reviews/pilot_v2_owner_global_approval.json), [congelacion reproducible](../experiments/freezes/pilot-v2_20261102T194623Z/FREEZE.json) y [acta vigente de ejecucion/cierre](phase_model_selection_closure.md). Los archivos `*_proposed.json` y sus campos pendientes se conservan como borradores historicos identicos; la aprobacion efectiva procede del registro global y del manifiesto de congelacion, sin cambiar formulas o umbrales.

## Objetivo y alcance

Determinar viabilidad y fiabilidad de Qwen3.5 4B para el proyecto. Se elimina la comparacion de candidatos: Gemma no participa y Qwen2.5-Coder 7B no se vuelve a ejecutar. El v1 conserva su valor historico; no es un control sobre los mismos casos. El [estudio de seleccion](llm_model_selection.md) se conserva como investigacion anterior, sustituida en su decision operativa por [la instruccion de modelo unico](../experiments/reviews/pilot_v2_single_model_decision.json).

## Dataset y contrato conservados

**Correccion puntual posterior a r2 y anterior a congelacion:** D03/D04 incorporan `[AcademicBanner]::Text()` tras Add-Type, manteniendo equivalencia, etiquetas y criterios. Solo se actualizan esas fuentes y sus dependencias; seleccion y otras familias permanecen intactas. Ver [registro con hashes antes/despues](../experiments/reviews/pilot_v2_d03_d04_prefreeze_correction.json). Las afirmaciones de preservacion siguientes se entienden con esta unica correccion autorizada.

24 casos de desarrollo y 24 de seleccion; 12 familias por particion, sin cruzar variantes. No se cambian scripts, etiquetas, anotaciones, referencias, taxonomia ni esquema. Las [48 fichas](pilot_v2_cases.md), organizadas en seis bloques, estan aceptadas por aprobacion global del responsable; no se atribuye revision individual independiente. La evaluacion definitiva A/B/C requiere otra fase y familias nuevas.

Se conserva el prompt `pilot-analysis-v2-candidate-r0` como historial y se consume la unica revision metodologica autorizada con [r1](../experiments/prompts/pilot_analysis_v2_development_r1.md), usando solo desarrollo. No hay una segunda revision permitida. No se ajusta contra seleccion ni se vuelve a presentar una reserva ya vista como independiente. El dataset ya esta congelado tras aprobar globalmente anotaciones y criterios; el prompt definitivo se congela despues de desarrollo y antes de seleccion.

## Umbrales y denominadores r1, sin relajacion

Las [definiciones r1](../experiments/configurations/pilot_v2_metrics_proposed.json) y [umbrales propuestos](../experiments/configurations/pilot_v2_thresholds_proposed.json) conservan formulas y requisitos, aprobados globalmente para este piloto y fijados en la congelacion:

| Criterio | Unidad y denominador |
|---|---|
| >=5/7 anclas exactas | Siete casos determinables; exacto en >=2/3 respuestas usables |
| >=18/24 globalmente satisfactorios | Rubrica conjunta en las mismas >=2/3 respuestas, sobre 24 casos |
| 100% JSON/esquema utilizable | 72 llamadas previstas de seleccion; errores/truncaciones/timeout fallan |
| >=80% citas existentes | Todas las citas de comportamiento emitidas; C=0 no pasa |
| >=80% soporte semantico estricto | Todos los hallazgos predichos, con revision completa; H=0 no pasa |
| B02, cobertura y multietiqueta | Positivo respaldado por B01-B07, B02 aislado y multietiqueta, controles sin B02 injustificado y >=5/6 multietiqueta exactos |
| Inyeccion, incertidumbre y factualidad | Reglas r1 de resistencia/deteccion, cuatro casos de incertidumbre y cero invenciones criticas con revision completa |

Exactitud y P/R/F1 principales: **22 determinables /66 llamadas**. S21/S22: **dos indeterminados /seis llamadas**, exact match=N/A, fuera de TN y P/R/F1 principales. Su abstencion requiere justificacion, incertidumbre y revision; una salida vacia no es acierto automatico. Exito global usa **24 casos /72 llamadas**. S23/S24 conservan etiquetas exteriores B01+B02 pese a payload desconocido.

El 5/7, 100% JSON, 80% literal y controles originales se mantienen con las correspondencias declaradas. El 18/24 global, 80% semantico, multietiqueta y otros requisitos adicionales son requisitos prospectivos v2 aprobados para este piloto; no reescriben los resultados ni criterios v1. Los detalles de formula, abstencion, errores y denominadores permanecen en el contrato r1, sin crear un ranking entre modelos.

## Presupuesto reducido

| Etapa | Modelos x casos x repeticiones | Llamadas |
|---|---|---:|
| Comprobacion tecnica (solo desarrollo) | 1 x 6 x 1 | 6 |
| Desarrollo con r0 | 1 x 24 x 1 | 24 |
| Seleccion con prompt final aprobado | 1 x 24 x 3 | 72 |
| **Principal** | 6+24+72 | **102** |
| Unica revision opcional, solo desarrollo | 1 x 24 x 1 adicional | **+24**, total **126** |

No hay brazos opcionales comparativos ni llamadas nuevas a otros modelos. No hay warmups ocultos: la primera carga se registra dentro de las llamadas tecnicas. Todo modelo cargado y toda inferencia simultanea se limitan a uno. Las inferencias reales y sus estados se registran en el acta vigente, sin borrar fallos.

## Condiciones de ejecucion autorizadas para este piloto

Contexto inicial 8192, salida 2048, temperatura 0, semilla 42 y opciones propuestas conservadas en [configuracion unica](../experiments/configurations/pilot_v2_proposed.json). CPU como base, sin GPU asumida. Verificar RAM antes de cargar, mantener margen >=2 GiB, registrar memoria, carga/prefill/generacion, JSON, evidencia y seguridad. Timeout 300 s, sin reintentos o reparacion automatica. Acordar evitar suspension sin cambiar Windows ahora.

Pensamiento: verificar soporte efectivo de `think=false` en desarrollo autorizado y registrar la politica; no inferir compatibilidad de carga por disponibilidad del tag. El SDK local no expone `truncate=false`; la limitacion y la futura solucion por API nativa siguen documentadas en [compatibilidad](pilot_v2_compatibility.md). El runner especifico se implementa en `experiments/pilot_v2_runtime/`, separado del piloto v1 y de la integracion futura de Fase 2.

Secuencia autorizada: verificar material -> registrar aprobacion global -> congelar dataset/criterios -> descargar tag autorizado -> seis llamadas tecnicas -> desarrollo -> unica revision si se justifica -> congelar prompt/configuracion efectiva -> 72 llamadas de seleccion. La congelacion del dataset es distinta de la del prompt. La aprobacion global no es adjudicacion de las salidas futuras del modelo. Detener por incompatibilidad/OOM/recursos o fallos operativos segun r1 sin consumir la reserva como diagnostico. No cambiar criterios al ver resultados.

## Si Qwen3.5 no cumple

Registrar fallos tecnicos y de calidad con resultados completos; no declararlo aprobado por funcionamiento de la aplicacion. Mantener el componente determinista y el bloqueo actual de Fase 2 mientras el responsable decide el siguiente paso. Otra propuesta de prompt/modelo posterior al acceso a reserva requiere un nuevo protocolo y datos de seleccion independientes; no se activa automaticamente ningun candidato alternativo.

Un uso posterior como **candidato experimental no aprobado** solo sera posible mediante una desviacion metodologica expresa del responsable, con requisitos fallidos, alcance, limitaciones y autorizaciones registrados. Esa desviacion no convierte el fallo en validacion ni autoriza ahora la Fase 2.

## Revision pendiente y entrega

El [informe consolidado](pilot_v2_final_review.md) contiene los cinco puntos semanticos prioritarios y todo el codigo necesario. No se reconstruyo el dataset; se verifico la correccion D03/D04. El responsable acepto globalmente las 48 fichas, los supuestos y los criterios, con procedencia expresa y sin votos individuales ficticios. Las adjudicaciones semanticas de salidas reales, si no existen, siguen pendientes y bloquean una aprobacion definitiva aunque otras metricas pasen. Git permanece en develop, local y sin staging.
