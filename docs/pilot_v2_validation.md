> **Estado vigente tras la instruccion de cierre:** las secciones de preparacion siguientes son historicas. Dataset/criterios aprobados globalmente y congelados; experimento interrumpido por compromiso de memoria. [Acta actual](phase_model_selection_closure.md).

# Piloto v2 — verificacion de la preparacion

**2026-11-02. Resultado: propuesta coherente para revision humana; NO lista para inferencia.**

**Vigencia r2:** modelo unico Qwen3.5 4B, 102/126 llamadas; ver adenda r2 al final. Los apartados r0/r1 son registros historicos de comprobaciones, no brazos activos ni nuevas autorizaciones.

El cuerpo inicial conserva la verificacion de preparacion r0. La **adenda r1 al final** registra la verificacion de la revision metodologica posterior; sus nuevos totales no sustituyen resultados historicos de inferencia.

## Pruebas realmente realizadas

- Suite completa offline: **656 aprobadas, 0 fallidas, 0 omitidas**, en la pasada final de 5,37 s de pytest. Incluye las 488 regresiones existentes y **168 comprobaciones nuevas**. El tiempo es una observacion de pruebas, no un benchmark de inferencia.
- Reexportacion en modo lectura: **65 artefactos de autoria coinciden byte a byte**, sin escribirlos durante la comprobacion.
- Dataset: 48 IDs/rutas/hashes unicos, 24 casos y 12 familias por split; particiones sin familias compartidas; cobertura B01-B07; seis multietiqueta y seis negativos claros por split; ataques emparejados que solo agregan el comentario; redacciones adversarias diferentes entre splits.
- Evidencias: offsets, lineas, columnas, existencia de fragmentos, pertenencia al caso, relaciones locales y cobertura de etiquetas; referencias Base64 UTF-16LE iguales a sus fuentes decodificadas y separadas de recuperacion del modelo.
- Contratos/gates: JSON Schema igual al contrato historico, prompt candidato sin IDs/soluciones, proyeccion de entrada limitada al texto, presupuesto aritmetico, revisiones humanas pendientes y ejecucion deshabilitada.
- Exportador: cinco pruebas negativas sobre temporales aislados verifican que no sobrescribe notas/revisiones o congelacion. Los datos sinteticos de esas pruebas no se registran como aprobaciones del proyecto.
- Seguridad: inspeccion AST de imports/llamadas del preparador; ningun import de ejecucion de muestras, red, cliente LLM o motores. No hay runner del piloto v2.
- Auditoria de contaminacion: 576 comparaciones entre splits, sin duplicados canonicos ni banderas >=0,72 entre ellos. Dos banderas contra una fixture historica permanecen documentadas y pendientes de adjudicacion humana; no son prueba automatica de independencia semantica.

Comando final usado, desde la raiz, con un directorio temporal **nuevo** fuera del repositorio:

```powershell
$v2ReleaseTestTemp = Join-Path $env:TEMP ('powershell-insight-v2-release-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $v2ReleaseTestTemp) { throw 'Fresh temporary path unexpectedly exists.' }
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests --basetemp "$v2ReleaseTestTemp" --tb=short
.\.venv\Scripts\python.exe -B -m experiments.pilot_v2.build_dataset
git --no-optional-locks diff --check
```

Estos comandos ejecutan pruebas Python sobre datos de texto; no invocan una muestra PowerShell ni un modelo. `-B` y `no:cacheprovider` evitan cachés en el repositorio. La ruta temporal aleatoria se comprueba inexistente; no se borraron directorios del usuario. Se uso esta ubicacion explicita porque el directorio temporal global preexistente de pytest no era accesible desde el sandbox. La comprobacion historica de seguridad se conservo intacta; se ajusto una construccion del exportador que coincidia con su heuristica de nombres de ejecutables por una etiqueta Markdown, sin relajarla.

## Integridad y Git

- Rama **develop**, HEAD `0b2a67d5cbac841ff53c1a5e0f29ee65b3ac9bda` conservado.
- **140 archivos tracked conservan sus bytes**, comprobados por hash agregado contra `experiments/pilot_v2/preparation_baseline.json`. Incluye metodologia, historia, taxonomia, motores 1A/1B, evaluadores y pruebas anteriores.
- Los **seis hashes de resultados del piloto v1** coinciden con el manifiesto historico. No se regeneraron resultados ni se cambiaron ground truth/prompts historicos.
- El indice Git y el estudio local preexistente `docs/llm_model_selection.md` conservan sus hashes iniciales. No hay cambios staged ni archivos tracked modificados.
- Se conserva LF con atributos nuevos y acotados a v2, sin editar los atributos raiz/historicos. `git diff --check` pasa; los archivos nuevos se revisan ademas individualmente porque el diff normal no incluye untracked.
- Inventario de archivos nuevos y hashes: [pilot_v2_preparation_inventory.json](../datasets/metadata/pilot_v2_preparation_inventory.json). Excluye al propio inventario y al estudio preexistente; sus hashes son de preparacion, no un congelamiento aprobado.

Todas las acciones Git fueron de lectura/comprobacion. No se ejecutaron add, commit, push, merge, rebase ni operaciones destructivas.

## Limites del resultado

Las pruebas establecen coherencia, trazabilidad e integridad, **no validan semanticamente el ground truth ni miden modelos**. Los 48 casos y todos los grupos de evidencia siguen pendientes humanos; los criterios/parametros/brazos no estan aprobados ni congelados. La consulta final a `/api/ps` seguia sin modelos cargados.

No se descargaron pesos, actualizaron dependencias/Ollama, ejecutaron inferencias, muestras, A/B/C o Fase 2. Siguiente paso: revision del [protocolo](pilot_v2_protocol.md), [fichas](pilot_v2_cases.md) y [checklist](pilot_v2_review_checklist.md), con decisiones expresas del responsable antes de autorizar congelacion, descargas o ejecucion.

## Adenda — revision metodologica r1 (2026-11-02)

- **683 pruebas aprobadas**, cero fallidas/omitidas, en 5,80 s de pytest en la pasada completa de esta revision. Son 488 pruebas previas del proyecto y 195 del incremento v2: **27 nuevas en esta ronda** respecto de las 168 de preparacion. No son mediciones de modelos.
- La exportacion offline verifica **72 artefactos byte a byte**, incluidos seis bloques de ocho fichas y una revision tecnica por caso. Los 65 artefactos de la seccion inicial corresponden al exportador anterior.
- Comprobaciones nuevas de denominadores: 22 determinables/66 llamadas; dos indeterminados/seis llamadas; exito global sobre 24/72; cero denominadores no son 100%; errores no son negativos verdaderos ni abstenciones justificadas. Se prueba la exigencia de mayorias conjuntas en las mismas respuestas.
- Los **62 archivos protegidos** por `experiments/pilot_v2/review_round1_baseline.json` conservan sus hashes: 48 scripts, ocho referencias y seis archivos de manifiesto/anotaciones/prompt/contrato/revision. No se cambiaron etiquetas o familias. Los snapshots de configuracion/umbrales r0 identifican la propuesta sustituida, no una aprobacion.
- La aceptacion preliminar de estructura/candidatos se registra por separado. Los 48 casos siguen pendientes y no hay nombre, firma, congelacion, descarga o inferencia autorizados.
- S04/S20 tienen comparaciones de fuente y hashes, recomendacion tecnica de conservar y **decision humana pendiente**. Sus textos no se sustituyeron.
- Se conserva la comprobacion de los seis hashes v1 y de todos los archivos tracked/indice contra el baseline inicial. Los motores 1A/1B y el prompt v1 permanecen intactos.
- Enlaces y whitespace se revisan tambien para untracked; las comprobaciones Git no modifican staging ni historial. Los cambios de esta ronda quedan en [registro de cambios r1](../datasets/metadata/pilot_v2_review_round1_changes.json).

La [revision final propuesta](pilot_v2_final_review.md) y el [checklist por bloques](pilot_v2_review_checklist.md) son la entrada de revision humana. La referencia logica de metricas opera solo sobre evaluaciones hipoteticas aportadas; no lee salidas reales, adjudica semantica ni implementa un runner. El prompt candidato r0 permanece identico, con cero de una revisiones experimentales consumidas.

## Adenda r2: simplificacion definitiva a modelo unico (2026-11-02)

- **196 pruebas pertinentes de piloto v2 aprobadas, cero fallidas u omitidas, en 0,96 s**: 195 existentes de preparacion/metricas y una comprobacion nueva de decision unica, integridad de reglas r1 y ausencia de autorizacion de ejecucion. No se repitio una auditoria general ni la suite completa de Fases 0B/1A/1B. Estos tiempos son de pytest, no inferencias.
- **72 artefactos coinciden byte a byte** en el modo de comprobacion offline. Solo se escribieron el indice y checklist de revision desde el generador; no se reconstruyo el dataset.
- Se mantienen los **62 hashes protegidos** de fuentes, referencias, manifiestos/anotaciones, prompt, contrato y revision. Los 48 casos siguen pendientes humanos. Los seis bloques completos no cambiaron.
- La configuracion contiene exclusivamente `qwen3.5:4b-q4_K_M`, con 6+24+72=102 llamadas y una unica revision opcional de desarrollo +24=126. Gemma y nuevas ejecuciones Qwen2.5 no forman parte del plan.
- El hash completo del contrato de metricas r1 y el hash canonico de `mandatory_proposed` coinciden con los registrados en la decision r2. Solo cambia la regla de decision de seleccion del archivo de umbrales. No se relajan requisitos.
- Los 140 archivos versionados, HEAD, rama develop, indice Git, estudio original y seis resultados v1 conservan sus hashes anteriores. No hay cambios staged ni archivos versionados modificados. No se ejecutaron operaciones Git de escritura/publicacion/integracion.
- Comprobacion final de enlaces locales y whitespace: aprobada; incluye los archivos untracked, que el diff ordinario omite. El inventario actualizado contiene hashes de preparacion, sin ser congelacion humana.

Comandos de prueba realmente utilizados, con temporal nuevo comprobado inexistente:

```powershell
$v2SingleModelTemp = Join-Path $env:TEMP ('powershell-insight-v2-single-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $v2SingleModelTemp) { throw 'Fresh temporary path unexpectedly exists.' }
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests/pilot_v2 --basetemp "$v2SingleModelTemp" --tb=short
.\.venv\Scripts\python.exe -B -m experiments.pilot_v2.build_dataset
```

No se descargaron modelos, hicieron llamadas a Ollama, ejecutaron inferencias/muestras, congelaron datos/prompt ni inicio Fase 2. Las observaciones de compatibilidad anteriores no se repitieron. Solo la eleccion del modelo esta decidida; anotaciones, criterios y autorizaciones siguen pendientes. El [informe consolidado](pilot_v2_final_review.md) presenta las decisiones y el codigo completo de los cinco puntos prioritarios.

## Adenda: D03/D04, invocacion explicita antes de congelacion (2026-11-02)

Correccion puntual autorizada por el responsable: agregar `[AcademicBanner]::Text()` tras Add-Type en la familia de desarrollo V2-DEV-F02. Se conserva B02 y riesgo benigno; no cambia ningun criterio, presupuesto, prompt, caso de seleccion u otra familia. La confirmacion humana de las 48 fichas y la congelacion siguen pendientes.

- **197 pruebas del piloto v2 aprobadas, cero fallidas/omitidas, en 0,83 s.** La prueba nueva exige definicion del metodo, llamada posterior a compilacion, equivalencia exacta plain/decoded y las tres evidencias B02 conjuntamente. Las pruebas existentes comprueban hashes, offsets Unicode, lineas/columnas, derivacion Base64 UTF-16LE y consistencia JSON/CSV.
- **72 artefactos de autoria coinciden byte a byte** en comprobacion sin escritura. Solo se escribieron los diez artefactos dependientes que cambiaron; no se reescribieron otras fuentes o fichas.
- El checkpoint r1 original permanece intacto. De sus 62 archivos, **55 conservan el hash original y siete tienen hashes anteriores/nuevos explicitamente registrados**: D03, D04, referencia D04, manifiestos JSON/CSV, anotaciones y revision humana (solo los dos hashes de fuente).
- El [registro de correccion](../experiments/reviews/pilot_v2_d03_d04_prefreeze_correction.json) conserva los hashes canonicos previos de los registros de 46 casos, sus anotaciones/revisiones y las otras 23 familias, que siguen coincidiendo. Las 24 fuentes de seleccion y todas sus referencias permanecen intactas. Los 18 archivos de contratos/parametros/prompt/historia identificados en el registro conservan sus bytes.
- Se actualiza exclusivamente el informe de similitud textual dependiente de las dos fuentes nuevas, sin modificar datos historicos ni decisiones de S04/S20. No se realiza una auditoria general de fases anteriores.
- Comprobaciones finales: 140 archivos versionados, HEAD, develop, indice y seis hashes de resultados v1 intactos; nada staged. Enlaces locales y whitespace de archivos del piloto aprobados; inventario de preparacion actualizado sin congelacion.

Comandos de prueba usados, con temporal nuevo comprobado inexistente:

```powershell
$v2MethodCorrectionTemp = Join-Path $env:TEMP ('powershell-insight-v2-method-' + [guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $v2MethodCorrectionTemp) { throw 'Fresh temporary path unexpectedly exists.' }
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests/pilot_v2 --basetemp "$v2MethodCorrectionTemp" --tb=short
.\.venv\Scripts\python.exe -B -m experiments.pilot_v2.build_dataset
```

No se interpreto ni ejecuto ninguna muestra PowerShell, compilo C#, realizo inferencia o descargo modelo. No se congelo el dataset, aprobo una ficha, consumio una revision del prompt ni inicio Fase 2. No se ejecutaron add, commit, push, merge ni rebase. Los totales de adendas anteriores se mantienen como historia de sus respectivas comprobaciones.

## Cierre operativo autorizado: ejecucion interrumpida (2026-11-02)

Se registraron aprobacion global y congelacion, se implementaron runner/evaluador separados de v1 y se descargo exclusivamente Qwen3.5 4B. Antes de seleccion pasaron 731 pruebas, y 72 artefactos de autoria coinciden byte a byte. Los casos/referencias/anotaciones y criterios permanecieron inmutables tras congelacion. El prompt r1 se congelo despues de la unica revision de desarrollo.

Resultados reales: 58 intentos, 57 respuestas recibidas, 55 utilizables; 2 truncamientos D24 en desarrollo. Seleccion: 4/72 intentos, 3 utilizables y 1 cancelado por compromiso disponible minimo 1,9423 GiB. RAM fisica minima 3,0163 GiB; no OOM observado. Se detuvieron 68 llamadas pendientes, sin reintento, reparacion, cambio de parametros o cierre de aplicaciones. Se libero solo la residencia del modelo propio mediante control sin generacion.

Decision: PENDIENTE / INCONCLUSO; Fase 2 bloqueada/no iniciada. Las tres propuestas de hallazgo semantico son AI-assist, no adjudicaciones humanas. Las metricas sobre llamadas no realizadas son bookkeeping del plan con denominadores fijos, no resultados observados. El informe final y los archivos exactos constan en el acta y recibos del cierre; los inventarios anteriores se preservan como checkpoints de preparacion, no como inventario actual posterior a esta instruccion.

Pasada final posterior a la interrupcion y liberacion del modelo: **731 pruebas aprobadas, cero fallidas/omitidas, 4,55 s**, incluidas 488 regresiones y 243 de v2. No hay modelos residentes ni inferencias adicionales. El recibo `experiments/results/pilot_v2/pilot-v2_20261102T194623Z/final_verification.json` y su inventario registran integridad final, sin staging ni reescritura historica.
