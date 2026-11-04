# Fase 4 — preparación entregada para revisión

**Preparación técnica y metodológica iniciada por autorización del responsable. No hay nuevas inferencias reales, referencias aprobadas automáticamente ni evaluación independiente ejecutada.** Se mantiene Qwen2.5-Coder 14B como único modelo exploratorio y se conserva el significado original de H1/H2.

## Material que debe revisarse

1. [Protocolo prospectivo](phase4_protocol_proposed.md): hipótesis exactas, tratamientos A/B/C, orden, métricas, contraste, recursos, conservación y criterios de cierre.
2. [Tabla de los 16 scripts y sus referencias propuestas](phase4_references_proposed.md), con una ficha completa por ID. Incluye texto exacto, hash, justificaciones de inclusiones/exclusiones, ausencias, evidencias, recuperación y activación.
3. [Independencia: audit y revisión requerida](phase4_independence_review.md): corpus previo, normalización, vecinos cercanos, diferencias lógicas y límites.
4. [Procedimiento de revisión personal](phase4_human_review.md): aceptación prospectiva de referencias y adjudicación posterior de afirmaciones bajo política estricta/permisiva.

Datos y configuración exactos: [cases.json](../artifacts/phase4_preparation/proposal/cases.json), [orden](../artifacts/phase4_preparation/proposal/order.json), [configuración](../artifacts/phase4_preparation/proposal/configuration.json), [32 solicitudes propuestas](../artifacts/phase4_preparation/proposal/requests/) y [recuperaciones 1A](../artifacts/phase4_preparation/proposal/recoveries/).

## Diseño propuesto y presupuesto exacto

**16 textos distintos → 16 A estáticos + 16 B + 16 C. Máximo: 32 intenciones reales LLM.** No se autorizan ahora. Las 48 salidas futuras no constituyen 48 muestras independientes.

Ocho textos tienen recuperación 1A no vacía y ocho sin recuperación relevante. Hay 14 conjuntos de etiquetas determinables y dos indeterminados fijados de antemano; 15 bloques de dependencia conservadores en total, 13 entre los determinables. Cada B/C usa el mismo original, modelo/digest, política, esquema y parámetros; solo C añade 1A. Ocho unidades tienen B primero y ocho C primero. No se envían referencias ni etiquetas 1B y no se reutilizan respuestas previas de B.

| Categoría | Positivos determinables propuestos |
|---|---:|
| B01 | 2 |
| B02 | 2 |
| B03 | 2 |
| B04 | 2 |
| B05 | 2, además de un mínimo conocido en F4-16 indeterminado |
| B06 | 5 |
| B07 | 2 |

Los tres negativos de conjunto vacío son F4-07, F4-13 y F4-14. F4-11 consulta tareas/firewall sin modificarlos; F4-12 usa credencial interactiva solo para autenticar remoting. F4-15/F4-16 evalúan falta de información, no negativos benignos. Los escenarios son sintéticos y las etiquetas caracterizan operaciones, no malware confirmado o efectos reales.

## Independencia y revisiones prospectivas

Se auditó únicamente material presente antes de esta preparación: selección, desarrollo, diagnósticos y literales de pruebas. Se comparan hashes exactos, programas normalizados y vistas decodificadas nuevas/anteriores. No se acepta como independencia un simple cambio de identificadores/literales. El archivo de audit conserva los vecinos más cercanos y las similitudes internas; el responsable debe revisar la novedad lógica antes del congelado.

Una candidata inicial F4-08 se parecía demasiado al wrapper ScriptBlock.Create de V2-S04; se sustituyó por generación IL e invocación de suma local. También se resolvieron límites de recuperación/contexto antes de congelar. Se preservaron los borradores y motivos en [preparation_revisions](../artifacts/phase4_preparation/preparation_revisions/). No se observó ninguna respuesta nueva del modelo para hacer esos cambios, ni se ajustaron taxonomía, política o parámetros para aprobarlo.

La autoría de las propuestas y la revisión automática son del asistente. No se atribuyen a un anotador humano independiente. La independencia semántica sigue pendiente de revisión, y no se demuestra independencia respecto del preentrenamiento de Qwen. Las ocho adjudicaciones personales del diagnóstico Qwen14 siguen pendientes y separadas.

El responsable aclaró que acepta archivos de texto `.ps1.txt`, objetivos de laboratorio inexistentes y análisis estático únicamente. Se aplicó ese criterio; no se crearon archivos ejecutables `.ps1` ni se ejecutaron muestras, recuperaciones, IL, compilaciones o contenido del modelo.

## Controlador y verificación

Paquete [experiments/phase4](../experiments/phase4/): preparación, auditoría, protocolo, controlador, métricas, evaluación y reportes. Reutiliza `AnalysisService`, motores estáticos, `Qwen14Adapter`, contrato JSON, contexto, validación literal, monitores y bloqueos existentes. No modifica frontend ni proveedores históricos.

El ledger se reserva antes de enviar bytes; verifica hashes/orden/propiedad del bloqueo y permite como máximo 32 intenciones, sin reintentos. Escribe un resultado por unidad/modo y checkpoint por hash. Detecta duplicaciones, respuestas anteriores a la campaña, checkpoints ausentes, intención huérfana y cambios de fuente/autorización. Un STOP crítico no se reanuda automáticamente; una continuación tras cierre abrupto limpio exige autorización específica y conciliación, sin repetir una intención.

Las simulaciones usan transportes B/C ficticios y red prohibida en copias temporales. A utiliza el motor estático existente para verificar la orquestación; sus etiquetas de prueba no se utilizan para establecer referencias ni se publican como resultados científicos nuevos. Los revisores/aceptaciones ficticios de esas copias se llaman explícitamente `SIMULATED`; las plantillas canónicas permanecen en `false` y no se creó un FREEZE oficial.

Se prueban presupuesto/orden, equivalencia B/C, separación de datos, campañas de baja calidad que completan sin “APTO”, rechazos terminales, memoria insuficiente, pérdida de margen, timeout, herramientas no autorizadas, cambios de hashes/autorización, intención huérfana, métricas con rechazo/indeterminación, macro, dependencia por bloque, H2 sin adjudicación y detección de renombrados/programas recién decodificados.

Los [resultados finales de verificación](../artifacts/phase4_preparation/validation_final.json) y la [integridad final](../artifacts/phase4_preparation/integrity_final.json) documentan regresiones, presupuestos y conservación. El registro de una observación de hardware de solo lectura no garantiza disponibilidad futura; el preflight completo debe repetirse justo antes de cada despacho real.

## Métricas y cierre científico

Se prepara clasificación micro/macro, conjuntos exactos, FP/FN por comportamiento, usabilidad/rechazos, controles indeterminados, cobertura A y exactitud calificada por cobertura. También citas literales/procedencia, reconstrucciones, riesgo/incertidumbre y adjudicación semántica. Los rechazados son `null`, no un `[]` correcto. La política permisiva y las parejas solo utilizables se informan como análisis secundarios, sin sustituir el principal.

H1 contrasta diferencia pareada de F1 micro C−B; H2 requiere inventarios personales completos de afirmaciones factuales y contrasta su número sin respaldo, C−B. Se prepararon sensibilidades condicionales por intercambio de bloques, bootstrap pareado y ajuste por dos hipótesis. No hay aceptación automática ni umbrales de aprobación del modelo. La literalidad no sustituye semántica; un resultado no evaluable de H2 o un efecto negativo es un resultado válido que debe reportarse, no corregirse con nuevas campañas.

La preparación no genera estadísticas empíricas H1/H2 con los textos nuevos. Los únicos números de efecto calculados en pruebas son datos sintéticos ficticios de verificación de fórmulas, identificados como simulaciones.

## Condiciones para autorizar una única campaña futura

1. Revisar personalmente las 16 referencias, seguridad e independencia/agrupación. Copiar y completar [reference_review.template.json](../artifacts/phase4_preparation/reference_review.template.json) en un archivo nuevo, sin modificar respuestas históricas.
2. Resolver las observaciones antes de ver salidas y, si cambia algo, versionar la candidata. Revisar su nuevo hash y sellar mediante `seal` únicamente tras aprobación expresa. La candidata actual es una fotografía propuesta, no una congelación aprobada.
3. Autorizar separadamente el FREEZE y un máximo exacto de **32 intenciones locales**, con fecha, declaración expresa y exclusividad. La [plantilla de autorización](../artifacts/phase4_preparation/execution_authorization.template.json) no es un permiso; todos sus indicadores de autorización están en `false`.
4. Aprobar un preflight fresco: RAM, compromiso, residentes, digest/cuantización/capacidades, disco y bloqueos. Sin recursos o verificación no se fuerza la carga, no se cierran programas y no se modifica Windows.
5. Tras la futura campaña, adjudicar las 32 respuestas según la rúbrica y conservar resultados negativos, fallos y no evaluables. Cerrar la Fase 4 con sus límites antes de pasar al pulido de Fase 5.

Comandos preparados, **no ejecutados para generación en este encargo**:

```text
python -m experiments.phase4 seal --personal-review <revision_personal.json>
python -m experiments.phase4 run --authorization <autorizacion_expresa_32.json>
python -m experiments.phase4 evaluate --personal-reviews <directorio_de_adjudicaciones>
```

Se ejecutan con `PYTHONPATH=backend;.` desde la raíz. No se debe usar `run` con plantillas sin completar ni utilizar una aprobación ficticia de pruebas.

No se realizaron solicitudes Gemini, descargas o eliminaciones de modelos, cambios visuales de frontend ni operaciones Git de escritura. Los cambios siguen locales en `develop`, sin staging. La única autorización pendiente es la revisión y el permiso explícito para esta campaña; no se reabre la búsqueda de modelos.

## Validación final y trazabilidad

| Comprobación | Resultado |
|---|---:|
| Regresión backend completa | **1.087 aprobadas** |
| Cierre con la candidata final | **19 simulaciones aprobadas** |
| Frontend sin modificaciones | **29 pruebas aprobadas** |
| Parser, sin evaluar los textos | **16/16 sin errores sintácticos** |
| Archivos preexistentes preservados | **9.394 sin cambios** |
| Nuevas inferencias reales | **0** |
| Gemini | **5/12, hash intacto** |

Evidencias: [backend](../artifacts/phase4_preparation/backend_regressions_verified.xml), [cierre de la candidata](../artifacts/phase4_preparation/candidate_closeout.xml), [validación estructurada](../artifacts/phase4_preparation/validation_final.json), [parser sin ejecución](../artifacts/phase4_preparation/powershell_syntax_only_final.json) e [integridad](../artifacts/phase4_preparation/integrity_final.json). La única advertencia del pase backend es una deprecación de Starlette/httpx; no produjo fallos. Los pases intermedios y sus correcciones de seguridad/novedad se conservaron, sin modificar o debilitar pruebas existentes.

Candidata pendiente de aprobación: `c7c0dc327291f7647d5093d2d729185d297fc70f55853f727ef511659411da64`, correspondiente a [CANDIDATE_MANIFEST.json](../artifacts/phase4_preparation/CANDIDATE_MANIFEST.json). No es un FREEZE aprobado ni autoriza generación. Los controles finales verificaron que ambas aprobaciones de las plantillas permanecen en `false`, que no hay carpeta de ejecución oficial y que los 16 hashes de texto son únicos.

Se contrastaron fuentes técnicas primarias sin ejecutar sus ejemplos: el ajuste Holm se describe como procedimiento escalonado Bonferroni en [statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html); la firma de creación del método dinámico, en [Microsoft .NET](https://learn.microsoft.com/en-us/dotnet/api/system.reflection.emit.dynamicmethod.-ctor?view=net-9.0). El enlace filtro/consumidor y la identidad compartida de creación WMI se documentan en [Microsoft WMI: binding](https://learn.microsoft.com/en-us/windows/win32/wmisdk/binding-an-event-filter-with-a-logical-consumer) y [seguridad de eventos](https://learn.microsoft.com/en-us/windows/win32/wmisdk/receiving-events-securely). Estas fuentes respaldan la revisión técnica, no sustituyen la aprobación personal de las referencias.
