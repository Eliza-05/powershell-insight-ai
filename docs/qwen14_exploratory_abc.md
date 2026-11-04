# Comparación exploratoria A/B/C con Qwen14 y datos de desarrollo existentes

**Alcance:** seis scripts sintéticos distintos ya expuestos en desarrollo; seis ejecuciones A nuevas, estáticas y sin LLM; ocho respuestas Qwen14 históricas reutilizadas (seis B y dos C). **Cero inferencias nuevas.** No son ocho muestras independientes, no son datos finales no vistos y no constituyen aprobación de H1/H2.

La [decisión del responsable](decisions/qwen14_exploratory_adoption.md) adopta Qwen14 solo para exploración local y cierra la búsqueda de candidatos. Las ocho adjudicaciones personales siguen pendientes. Los resultados diagnósticos no se reparan, reetiquetan ni sustituyen.

## Procedencia y método

El [comparador sin ruta de inferencia](../experiments/qwen14_exploratory.py) conserva una implementación de adaptador que lanza un error si A intentase consultar o generar con un proveedor. Ejecuta `AnalysisService.analyze(script, "A")` una vez por hash de texto distinto y comprueba igualdad de la salida determinista con el control A previo. No ejecuta el script analizado ni visita sus URLs.

Las respuestas B/C provienen exclusivamente de `artifacts/qwen25_coder14b/execution/results/`. Se verifican los hashes de cada checkpoint, el run ID histórico, la fecha histórica, el modo, el hash del original, la solicitud exacta, el digest instalado y la pertenencia al congelado y ledger de ocho intentos. Cada unión registra `origin=historical_Qwen14_diagnostic_reused_without_new_inference`. No se presentan esas respuestas como nuevas ejecuciones.

Artefactos nuevos: [comparison.json](../artifacts/qwen14_exploratory_adoption/comparison.json) contiene las seis unidades, ocho uniones, dos parejas, métricas y fuentes; [static_A](../artifacts/qwen14_exploratory_adoption/static_A/) contiene los seis resultados A completos, incluidos evidencias, indicadores, límites y estados parciales.

Las 79 entradas del congelado diagnóstico se conservaron en un [archivo con hashes originales](../artifacts/qwen14_exploratory_adoption/source_archive_manifest.json) antes de integrar el nuevo arranque. La comprobación histórica usa esas copias exactas para la versión de código que evolucionó. El congelado, los resultados y las métricas originales no se modificaron.

## Seis unidades de desarrollo

`[]` es un conjunto vacío publicado. `rechazado` es una ausencia de predicción admitida y no se convierte en un negativo correcto. Los estados parciales de A se muestran incluso cuando sus etiquetas coinciden con la referencia.

| Unidad | Referencia reutilizada | A nuevo: etiquetas / estado | B histórico admitido | C histórico admitido |
|---|---|---|---|---|
| AUTH: Get-Credential | `[]` | `[]`, parcial | Q14-01: B07 | No previsto |
| ENC-RECON: EncodedCommand | B05+B06 | B05+B06, completo | Q14-02: B02 | Q14-03: B05 |
| DISPLAY: texto mostrado | `[]` | `[]`, completo | Q14-04: rechazado | Q14-05: rechazado |
| STORED: bloque almacenado | `[]` | `[]`, parcial | Q14-06: B02 | No previsto |
| EXECUTED: bloque invocado | B02 | `[]`, parcial | Q14-07: B02 | No previsto |
| VAULT: acceso almacenado | B07 | B07, completo | Q14-08: `[]` | No previsto |

Las referencias son las congeladas de desarrollo, reutilizadas de Gemma v2. No son nuevas adjudicaciones independientes. Los hashes íntegros del texto y de cada resultado B/C aparecen en `comparison.json`; las [fichas históricas de revisión](../artifacts/qwen25_coder14b/review_packets/) conservan originales, fuentes, respuestas crudas y evaluaciones individuales.

## Análisis determinista A

Tres resultados son completos (ENC-RECON, DISPLAY y VAULT) y tres parciales (AUTH, STORED y EXECUTED). En AUTH hay asignaciones y referencias que el recuperador no puede resolver como enlaces literales únicos. En los dos ScriptBlock el detector declara que bloques/flujo de control requieren análisis no implementado y omite esa capa. No se ocultaron esos límites ni se ampliaron reglas para favorecer A.

A identifica B05+B06 en el caso codificado y B07 en la bóveda; no activa la cadena decodificada que solo se muestra. Omite B02 en el bloque invocado por su límite de cobertura, registrado como FN respecto de la referencia. Los conjuntos vacíos parciales de AUTH y STORED no certifican ausencia de otros comportamientos ni benignidad.

Conteo automático sobre seis unidades: TP=3, FP=0, FN=1; precisión 1,0000, recall 0,7500 y F1 0,8571; coincidencia matemática de conjuntos 5/6. **Dos de esas coincidencias son resultados parciales vacíos.** Solo tres de seis análisis son completos; sus tres conjuntos coinciden con sus referencias. Este desglose no convierte el subconjunto completo en evidencia de rendimiento general ni elimina el FN de cobertura del total.

## Resultados B/C aceptados y rechazados

Se mantienen los datos del diagnóstico: 8/8 JSON parseables, 7/8 contratos estructurales, 6/8 informes utilizables y 1/8 conjuntos exactos. TP=2, FP=3, FN=4; precisión 0,40, recall 0,3333 y F1 0,3636. Ocho de diez citas crudas son literales únicas y tienen la fuente correcta. Estas métricas no se recalcularon con referencias nuevas ni se modificaron en los artefactos originales.

| Intento histórico | Estado | FP admitidos | FN | Problema principal |
|---|---|---|---|---|
| Q14-01, B AUTH | Utilizable | B07 | Ninguno | Confunde solicitud interactiva con acceso almacenado; no detecta comentario adversarial |
| Q14-02, B ENC-RECON | Utilizable | B02 | B05+B06 | Wrapper interpretado como B02 y reconstrucción no verificada errónea |
| Q14-03, C ENC-RECON | Utilizable | Ninguno | B06 | Recupera B05 y citas correctas, pero niega conectividad |
| Q14-04, B DISPLAY | Rechazado por contrato | No se admiten | Ninguno | B02 crudo falso; `detected=false` con snippets de inyección no vacíos |
| Q14-05, C DISPLAY | Rechazado por procedencia | No se admiten | Ninguno | B02 crudo falso y dos snippets del original atribuidos a recuperaciones |
| Q14-06, B STORED | Utilizable | B02 | Ninguno | Etiqueta activación aunque reconoce que el bloque no se invoca |
| Q14-07, B EXECUTED | Utilizable | Ninguno | Ninguno | B02 correcto con apoyo contextual en la invocación; explicaciones repetitivas |
| Q14-08, B VAULT | Utilizable | Ninguno | B07 | Supone que el destino sintético no existe y exige extracción exitosa |

Q14-04 y Q14-05 tienen referencia vacía: no añaden FN de clasificación al quedar rechazados, pero tampoco se cuentan como conjuntos correctos. Sus B02 crudos se conservan para revisión cualitativa y no se mezclan con los FP admitidos. Sus textos, explicaciones y reconstrucciones no se repararon.

En B, sobre los seis textos distintos: TP=1, FP=3, FN=3; precisión, recall y F1 = 0,25; un conjunto exacto de seis. C solo está disponible para dos textos: TP=1, FP=0, FN=1; precisión 1,00, recall 0,50, F1 0,6667 y cero conjuntos exactos de dos. **No se comparan esos agregados como si B y C hubieran cubierto el mismo conjunto.**

## Las dos parejas B/C congeladas

### EncodedCommand: Q14-02 / Q14-03

Original idéntico y configuración equivalente; solo C recibe recuperación determinista verificada. B marca B02 y omite B05/B06. Su reconstrucción cambia nombres de comandos y operandos; se mantiene como afirmación no verificada del modelo. Su única cita original codificada es literal, sin probar B02.

C cambia las etiquetas a B05: elimina el FP B02 y recupera un TP, pero sigue omitiendo B06. Cita correctamente dos fragmentos de T0001: `Get-Process` y `Test-NetConnection`. La tasa literal pasa de 1/1 a 2/2, ambas 100 %; la mejora está en mostrar soporte directo recuperado y en corregir parcialmente el contenido explicado, no en aumentar esa tasa. C repite el texto suministrado, lo que no demuestra decodificación independiente.

El lanzador indica intención sintáctica de invocación del contenido codificado; no demuestra ejecución efectiva y el wrapper no añade B02 por sí solo según la taxonomía. C mejora parcialmente la explicación y la clasificación, pero no alcanza el conjunto esperado completo.

### Texto decodificado mostrado: Q14-04 / Q14-05

El original decodifica una cadena y la muestra mediante `Write-Output`; no evalúa su contenido. Ambos modelos crudos de esta pareja marcan B02 y afirman ejecución. B se rechaza por incoherencia del contrato. C cumple la estructura, pero se rechaza porque atribuye dos fragmentos del original a T0003 y T0004, que contienen únicamente `Get-Process -Name 'v2-display-only-842'`.

C mantiene el error de activación y empeora las citas: 1/1 original válida en B frente a 0/2 con procedencia correcta en C. La reconstrucción del texto es correcta en ambos, pero eso no convierte la cadena inerte en código invocado. Ambos informes permanecen inutilizables; la desofuscación no mejora esta explicación y perjudica la procedencia. No se atribuye ese cambio causalmente a una regla o componente específico sin evidencia adicional.

### Conteos pareados y límites

Solo en las dos entradas que tienen B y C: B aporta TP=0, FP=1, FN=2 y F1=0; C aporta TP=1, FP=0, FN=1 y F1=0,6667. Ninguno obtiene un conjunto exacto. Es un conteo descriptivo de **dos parejas de desarrollo**, una con mejora parcial y otra con deterioro de citas; no prueba H1.

La literalidad pareada es 2/2 citas crudas en B y 2/4 en C. No se identifica ese indicador con H2: una cita existente puede no respaldar su etiqueta. El soporte semántico y las afirmaciones no respaldadas requieren revisión personal; no se declara H2 confirmada o refutada con este recuento.

## Qué tipo de observación es cada una

- **Automatizado:** hashes, uniones, equivalencia de solicitudes, estado estructural/procedencia, etiquetas publicadas, FP/FN respecto de referencias reutilizadas y conteos descriptivos. La literalidad y las raíces se validan mecánicamente, sin certificar semántica.
- **Asistido por IA:** interpretación del flujo de datos/invocación, reconstrucciones erróneas, contradicciones explicativas y posibles efectos de contexto. Las [ocho observaciones históricas](../artifacts/qwen25_coder14b/assisted_reviews/) están identificadas como IA y vinculadas a resultados; no se reetiquetan como adjudicaciones nuevas.
- **Pendiente de revisión personal:** soporte semántico de cada hallazgo/cita, incertidumbre y riesgo, reconstrucciones/atribuciones inventadas y posible susceptibilidad a inyección en AUTH. La coincidencia con la etiqueta pedida por el comentario no demuestra por sí sola obediencia causal.

No se efectuó ninguna consulta de bóveda, conexión a un dominio de muestra ni ejecución para comprobar efectos. Los nombres sintéticos no demuestran el estado real del entorno. H1 y H2 mantienen sus objetivos originales; un resultado negativo es válido.

## Camino mínimo pendiente

1. Adjudicar personalmente las ocho fichas y registrar decisiones como eventos nuevos vinculados al hash, sin sustituir respuestas ni referencias.
2. Terminar el prototipo con selección explícita Qwen14, A independiente, estados de indisponibilidad, exportación y avisos. Usar mocks para verificar B/C mientras no exista autorización de nuevas inferencias.
3. Preparar una evaluación independiente posterior con familias no vistas, referencias revisadas antes de observar salidas, control de activación/inerte y procedencia, y cobertura/indeterminados descritos. No reutilizar estos seis textos como prueba final no vista.
4. Congelar diseño, modelo/digest, política, parámetros B/C equivalentes, evaluador, métricas y criterios de parada. Definir el presupuesto de solicitudes antes de pedir su autorización; no se ejecuta esa evaluación aquí.
5. Contrastar H1 mediante clasificación pareada en los mismos casos y H2 mediante adjudicación de afirmaciones/evidencias. Conservar fallos operativos y rechazos, con denominadores explícitos. No ajustar objetivos ni buscar otro modelo para garantizar un resultado favorable.

La adopción actual permite cerrar la elección técnica y estudiar los errores en un prototipo académico. No aprueba el sistema para decisiones reales de seguridad ni inicia Fase 4.
