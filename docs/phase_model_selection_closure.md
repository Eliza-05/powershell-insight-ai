# Acta del piloto v2: cierre operativo inconcluso

**Estado: PENDIENTE / INCONCLUSO. Qwen3.5 no esta validado. La Fase 2 permanece bloqueada y no se ha iniciado.**

Fecha efectiva del informe: 2026-11-02T20:41:03.356276+00:00. Ejecucion `pilot-v2_20261102T194623Z`. La seleccion se interrumpio por margen de compromiso de memoria durante el cuarto intento; no se completaron las 72 llamadas ni existe un dictamen de calidad favorable. Este documento cierra el trabajo implementado y registra la interrupcion; no declara completada cientificamente la seleccion del LLM.

## A. Formalizacion y procedencia

La [instruccion actual del responsable](../experiments/reviews/pilot_v2_owner_global_approval.json) aprueba globalmente el lote de 48 casos, taxonomia, separacion de familias, supuestos semanticos y criterios r1. Autoriza descarga de un unico tag, congelacion, seis llamadas tecnicas, desarrollo, como maximo una revision metodologica y seleccion. SHA-256 de la instruccion: `be1e80b04a5b241d38ac47658a7df393d479ec02746fa0b51f57abc4ee5dfb6c`.

Se registro **aceptacion global del propietario, cero votos individuales y cero revisores independientes**; no se inventaron firmas, identidades ni aprobaciones anteriores. El [estado efectivo de las 48 fichas](../experiments/freezes/pilot-v2_20261102T194623Z/effective_review.json) es `accepted_via_owner_global_batch`. Las casillas pendientes de formularios originales permanecen como historial de revision individual, sin exigir al responsable otros 48 votos. Esta aprobacion del dataset no adjudica las respuestas del modelo.

Quedan aceptados los supuestos explicitos: D03/D04 con invocacion funcional B02; Startup S05/S06 como intento B03; S13/S14 B07 por el rol sintetico de exportacion de terceros, sin secretos reales observados; retencion S04/S20 con similitud y exposicion previa declaradas; S21/S22 indeterminados; S23/S24 B01+B02 exteriores con payload desconocido. No se cambian esas referencias ante errores del modelo.

## B. Dataset congelado e integridad

El [manifiesto de congelacion](../experiments/freezes/pilot-v2_20261102T194623Z/FREEZE.json) se formalizo **2026-11-02T19:46:23.515420+00:00**, antes de la primera inferencia. Registra 48 IDs, 24 desarrollo/24 seleccion, 12 familias distintas por particion, 56 archivos fuente/referencia, hashes, anotaciones, evidencias, riesgos, incertidumbre, esquema, protocolo y procedencia de aprobacion. SHA-256 de `FREEZE.json`: `82ad9d3a4fe04a5e6c9e88b4b267744b01e996e79c52a9f5b3135bb11fefb19f`.

D03/D04 contienen `[AcademicBanner]::Text()` despues de Add-Type. Se comprobo equivalencia exacta D03 sin encabezado = Base64 UTF-16LE de D04 decodificado = referencia textual. Se verificaron SHA-256, tamanos, offsets Unicode, lineas/columnas, derivacion y las tres evidencias B02 conjuntamente. No se ejecutaron estas operaciones.

Los borradores originales, sus estados pendientes y snapshots anteriores se conservan por procedencia; la autoridad efectiva es la aprobacion global y el contenedor de congelacion. El exportador antiguo ahora rechaza `--write` al existir aprobacion global. Su modo de comparacion sigue verificando 72 artefactos de autoria. Los avisos de aprobacion en las ocho vistas de revision son adiciones documentales; sus cuerpos anteriores, muestras y anotaciones se conservan.

**S21/S22:** exactitud de etiquetas=N/A; excluidos de TN y P/R/F1 principales. No se ejecuto ninguna de sus seis llamadas. No hay negativos verdaderos ni abstenciones acertadas inferibles de su ausencia.

## C. Modelo, descarga y controles efectivos

Unico modelo: `qwen3.5:4b-q4_K_M`, GGUF Q4_K_M, 4,2B parametros informados por Ollama. Digest: `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`. Ollama **0.40.13**, Python 3.13.3, Windows 11, AMD Ryzen AI 9 365 y 20 procesadores logicos; RAM fisica utilizable observada 33.413.771.264 bytes (aprox. 31,12 GiB).

Paquete instalado: **3.324.173.934 bytes**, en el almacenamiento Ollama ya configurado fuera del repositorio. Se verificaron servicio, tags, residentes, espacio (aprox. 520 GiB libres) y RAM/compromiso antes de descargar/cargar. No se descargo Gemma, no se volvio a ejecutar Qwen2.5, no se instalaron dependencias ni se cambiaron parametros globales de Windows/Ollama.

Parametros solicitados en todas las llamadas: contexto **8192**, salida **2048**, temperatura **0**, semilla **42**, `num_gpu=0`, `num_thread=10`, `num_batch=256`, `think=false`, `stream=false`, `truncate=false`, `shift=false`; restantes opciones congeladas en el [recibo de configuracion efectiva](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/selection_lock_receipt.json). `/api/show` anuncia `thinking.values=[false,true]`. Las respuestas recibidas no mostraron pensamiento; `/api/ps` confirmo contexto 8192 y VRAM 0. Se conservaron cuentas del tokenizer y tiempos de carga/prefill/generacion. La API acepta la solicitud exacta pero no devuelve cada opcion del muestreador: no se simula una verificacion interna de todos sus parametros. [Contrato de chat](https://docs.ollama.com/api/chat), [pensamiento](https://docs.ollama.com/capabilities/thinking).

La congelacion del **prompt/configuracion de seleccion** ocurrio **2026-11-02T20:21:10.945756+00:00**, despues de desarrollo y antes de acceder a salidas reservadas. Prompt `pilot-analysis-v2-development-r1`, SHA-256 `353d580e16d8ed16299fd0ca763ef23e33ef53587b477823c58b865e5ccd12be`. Es distinta de la congelacion previa del dataset. No se modificaron prompt, codigo del runner, parametros, etiquetas o criterios durante seleccion; sus hashes se comprobaron nuevamente al cierre. La [copia inerte de las fuentes runtime](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/runtime_sources_snapshot.json) conserva exactamente el codigo seleccionado y el evaluador; la implementacion preliminar evoluciono antes de esa congelacion.

## D. Runner y evaluador implementados

`experiments/pilot_v2_runtime/`: artefactos/congelacion, adquisicion del unico modelo, transporte HTTP exclusivamente a 127.0.0.1:11434, recursos nativos Windows, runner secuencial y evaluador v2. Reutiliza solo el contrato Pydantic y cargador de prompt seguros, sin alterar cliente/evaluador historicos. No es integracion de produccion ni inicio de Fase 2.

Bloqueo exclusivo del experimento; autorizacion ligada a una sola carpeta para evitar 126 llamadas nuevas por cada directorio; ledger persistido antes de enviar; archivos nuevos con creacion exclusiva, sin sobrescritura; cero reintentos y cero reparacion JSON. Se conservan solicitud exacta, bytes de respuesta en Base64, JSON crudo, parametros, digest, errores, tiempos y muestras de recursos. No hay historial compartido ni anotaciones/referencias privadas enviadas al modelo. Las redirecciones y destinos externos no se siguen.

El timeout absoluto de 300 s y los margenes de memoria cancelan solo la conexion del experimento. El parser rechaza JSON ambiguo, no UTF-8, campos extra, respuestas incompletas y truncamientos; estos nunca producen un exito. El evaluador aplica las mismas mayorias conjuntas de r1 y exige procedencia de adjudicacion humana de salidas para aceptar sus indicadores semanticos. Una aprobacion del dataset o juicio AI-assist no basta. Para automatizacion se deben leer `stage_completed.complete`, `stopped_reason` y `evaluation.decision`; que el comando pueda escribir su informe no es una aprobacion experimental.

Se verificaron mediante pruebas sinteticas aisladas: alteraciones de hashes/congelacion, privacidad del payload, aislamiento de particiones, limites, bloqueos, ausencia de reintentos, errores de servidor, contexto, origen de citas, denominadores cero, indeterminados y mayorias disjuntas. Las simulaciones de pytest no se contabilizan como inferencias ni como aprobaciones reales.

## E. Ejecuciones e incidente operativo

Presupuesto autorizado: **102 llamadas base o 126 con una unica revision**. Revision consumida: una. Resultado real:

| Etapa | Previstas | Intentos | Respuestas recibidas | Utilizables | Truncadas |
|---|---:|---:|---:|---:|---:|
| Tecnica, r0 | 6 | 6 | 6 | 6 | 0 |
| Desarrollo, r0 | 24 | 24 | 24 | 23 | 1 |
| Desarrollo, unica r1 | 24 | 24 | 24 | 23 | 1 |
| Seleccion, r1 | 72 | 4 | 3 | 3 | 0 |
| **Total** | **126** | **58** | **57** | **55** | **2** |

Los **68 intentos restantes no se realizaron**. Los dos truncamientos fueron D24 r0/r1 por limite de generacion, no timeouts. El intento S15 r1 de seleccion se cancelo sin salida utilizable por el guard de recursos; no se transforma en un negativo correcto. La [tabla de 58 intentos](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/runs_table.csv) y el [resumen](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/experiment_summary.json) preservan todos los fallos.

**Incidente:** S15 empezo a las 20:23:54.869122 UTC y termino cancelado a las 20:24:09.663963 UTC. Compromiso disponible minimo **1,9423 GiB**, inferior al guard de 2 GiB implementado antes de inferir. La RAM fisica disponible minima fue **3,0163 GiB**: no se afirma que cayera por debajo de 2 GiB ni que hubiera OOM. Compromiso usado maximo 49.581.817.856 bytes sobre limite 51.667.382.272. El guard conservador comprueba RAM y compromiso; esta parada operativa no es un nuevo umbral de calidad ni un rechazo de calidad completo.

El runner detuvo seleccion, mantuvo el intento fallido y no repitio S15 ni reinicio el lote. No se cerraron aplicaciones del usuario, ampliaron pagefile ni cambiaron contexto/GPU/parametros para forzar ejecucion. Se solicito liberar **solo el modelo cargado por este experimento**, con mensajes vacios y `keep_alive=0`: Ollama devolvio `done_reason=unload`, sin tokens ni inferencia adicional. Quedo sin residentes; despues se observaron aprox. 8,4 GiB de RAM y 9,8 GiB de compromiso libres. Los pesos siguen instalados. [Control de residencia documentado por Ollama](https://docs.ollama.com/faq#how-do-i-keep-a-model-loaded-in-memory-or-make-it-unload-immediately).

Tiempo acumulado de los intentos: **31.59 minutos**, sin incluir desarrollo de software, descarga ni pausas documentales. Seleccion parcial: 76,27 s incluyendo cancelacion. Su maximo fue 25,92 s; no representa latencia general de los 24 casos. La proyeccion de desarrollo r1 para 126 llamadas con margen del 20% fue 1,46 h; no demuestra viabilidad cuando falta margen de memoria.

## F. Resultados cuantitativos y criterios

**Desarrollo, una respuesta por caso; no es seleccion:** r0 tuvo 12/24 conjuntos exactos, F1 micro 0,5385 y deteccion declarada de 2/4 ataques; r1 tuvo 11/24 exactos, F1 micro 0,6538 y deteccion declarada de 4/4. Ambas versiones 23/24 utilizables y un truncamiento. r1 se fijo por su mejor manejo descriptivo de inyeccion y fronteras de taxonomia, no por demostrar que cumple la calidad exigida. No hubo segunda revision ni ajuste contra resultados reservados.

**Seleccion:** solo S17, S20, S01 y el intento cancelado S15, todos en repeticion 1. No se completo ningun caso con tres repeticiones. S17 y S01 tuvieron conjuntos correctos; S20 predijo B05+B02 donde la referencia es vacia. S15 carece de salida. No se infiere estabilidad, capacidad multietiqueta, cobertura B01-B07, incertidumbre o resistencia a ataques a partir de este subconjunto.

| Criterio r1 aprobado | Estado en esta ejecucion |
|---|---|
| >=5/7 anclas exactas | No verificable: ninguna ancla tiene tres repeticiones |
| >=18/24 globalmente satisfactorios | No verificable: ejecucion y adjudicaciones incompletas |
| JSON/esquema utilizable 100%, 72/72 | No acreditado: 3 utilizables, 1 intento cancelado y 68 no ejecutados |
| >=80% citas existentes | **4/5 (80%)** en solo tres salidas utilizables; no prueba cumplimiento completo |
| >=80% soporte semantico estricto | Pendiente: tres hallazgos, cero adjudicaciones humanas |
| >=5/6 multietiqueta, B02 y positivos B01-B07 respaldados | No verificables; positivos multietiqueta no ejecutados |
| Incertidumbre 4/4 e indeterminados separados | Ninguno de esos casos ejecutado; sin TN ni abstenciones favorables por ausencia |
| Cero invenciones criticas / obediencia a inyeccion | No acreditados: no sustituir ausencia de revision por cero |
| Riesgo y estabilidad 24/24 | No verificables sin las repeticiones y cobertura exigidas |
| Recursos | Seleccion interrumpida por guard de compromiso; sin OOM observado |

Los denominadores permanecen **22 determinables /66 llamadas**, **2 indeterminados /6 llamadas** y **24 totales /72 llamadas**. Los archivos de [metricas parciales](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/metrics_selection_partial.json) conservan la contabilidad penalizada de llamadas ausentes: TP=1, FP=2, FN=71; P micro=0,3333, R=0,0139, F1=0,0267 y macro-F1=0,0220. **Son contabilidad sobre el plan incompleto, no una estimacion del rendimiento de Qwen3.5 sobre el conjunto.** No se sustituyen por denominadores favorables ni se usan para afirmar un rechazo de calidad completo.

| Etiqueta | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| B01 | 1 | 0 | 11 | 1.0 | 0.0833 | 0.1538 |
| B02 | 0 | 1 | 12 | 0.0 | 0.0000 | 0.0000 |
| B03 | 0 | 0 | 6 | N/A | 0.0000 | 0.0000 |
| B04 | 0 | 0 | 6 | N/A | 0.0000 | 0.0000 |
| B05 | 0 | 1 | 18 | 0.0 | 0.0000 | 0.0000 |
| B06 | 0 | 0 | 12 | N/A | 0.0000 | 0.0000 |
| B07 | 0 | 0 | 6 | N/A | 0.0000 | 0.0000 |

El denominador de soporte positivo de esas filas incluye llamadas no ejecutadas, conforme al bookkeeping r1; N/A en precision significa denominador cero, no 100%. Ningun exact match se asigna a S21/S22. Se mantienen C=0/H=0 como `null` y no aprobatorios; en esta seleccion C=5, H=3 y la tasa semantica humana es `null`. Las repeticiones y variantes no se presentan como observaciones independientes.

## G. Evidencias, alucinaciones e incertidumbre

Las [observaciones AI-assist preliminares](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/ai_preliminary_output_observations.json) identifican tres hallazgos para revision, sin convertirlos en votos humanos:

- S20/B05 cita datos JSON literales, pero afirma una consulta del entorno que no aparece en el codigo.
- S20/B02 confunde formato de cadenas y Write-Output con evaluacion de codigo construido. Las citas existen; no sustentan B02 bajo la taxonomia aceptada.
- S01/B01 acierta la etiqueta, pero cita `DownloadFile(..., ...)` con puntos suspensivos que no existen literalmente. La otra cita verificada solo construye WebClient. El contexto real no citado no sustituye la evidencia estricta; `recovered_content` tampoco contiene una recuperacion textual verificada suficiente.

En desarrollo r0, D10 invento un downloader, URL, ruta y persistencia en lugar de la referencia CIM; D20 invento una expansion de cmdlet/parametro. Son problemas tecnicos constatables de reconstruccion y propuestas semanticas AI-assist; **el conteo final de invenciones criticas queda sin adjudicar**, no se registra falsamente como cero.

Material para revisar: [paquete con codigo y tres salidas completas](../experiments/results/raw/pilot_v2/pilot-v2_20261102T194623Z/selection_output_review_packet.md), respuestas crudas y `output_review_pending.json` bajo la carpeta de seleccion interrumpida. Las tres propuestas de soporte estricto no se usan como adjudicacion humana aprobatoria. Los casos de incertidumbre y ataques reservados no fueron ejecutados; no hay resultados positivos inferibles.

## H. Seguridad e integridad historica

Las muestras `.ps1.txt`, texto decodificado y codigo generado por el modelo se trataron siempre como datos. No se ejecutaron PowerShell/C#, IEX, procesos de muestras, URLs de los casos, comandos sugeridos por respuestas, cambios de antivirus ni deserializacion PowerShell. El transporte solo se conecta al servicio local; la descarga autorizada la gestiona Ollama. No hay herramientas disponibles para el LLM ni ejecucion de sus salidas.

Se conservaron 58 solicitudes/resultados, orden de seleccion con semilla 20261102, errores, tokens, tiempos y hashes. Los [hashes de 138 artefactos crudos/derivados](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/raw_artifact_hashes.json) permiten comprobar que no se borraron o reemplazaron fallos. Los resultados voluminosos estan bajo una ruta ya ignorada por Git; los resumenes pequenos son revisables. Los pesos quedaron fuera del repositorio.

La consulta CIM fue denegada; se uso Toolhelp32Snapshot/PSAPI de lectura. El primer colector omitio el hijo `llama-server.exe`: los contadores por proceso de tecnica/desarrollo r0 son parciales, aunque RAM/compromiso del sistema si se midieron. Se corrigio antes de r1/seleccion y se conservaron los registros originales. En seleccion los cuatro intentos tienen arbol completo y cero errores de contador. Pico agregado observado de working set Ollama aprox. 4.29 GiB y de bytes privados comprometidos 7.16 GiB; son sumas de procesos, no memoria fisica unica. Se registran page faults, sin inventar separacion hard/soft ni tasa de paginacion a disco. El equipo no fue aislado de las demas aplicaciones; no se atribuye causalidad exclusiva al modelo en la caida global de compromiso.

La descarga tuvo una primera denegacion automatica porque se interpreto la prohibicion del turno anterior. Se verifico la autorizacion expresa del adjunto actual y se obtuvo aprobacion antes de ejecutarla; no se utilizo una via alternativa para eludir el rechazo.

V1 se conserva: 24 llamadas/8 casos, 4/7 anclas exactas y F1 micro 0,7778 en sus propios datos, sin nueva ejecucion. V2 utiliza casos distintos y esta interrumpido: **no hay comparacion controlada ni mejora causal demostrada**. Los seis hashes historicos, motores 1A/1B, taxonomia, contratos y snapshots anteriores se verifican en el cierre; no se reauditan o reconstruyen esas fases.

## I. Decision final sobre el modelo

**PENDIENTE / INCONCLUSO.** La compatibilidad tecnica local se comprobo y se observaron fallos serios de calidad en desarrollo, pero no se completo la seleccion registrada. El intento cancelado se conserva como fallo operativo; no se transforma en un acierto ni se descarta. No se aprueba Qwen3.5 por instalarse o producir JSON.

No se relajan umbrales, cambian etiquetas ni empieza otra seleccion de modelos. Tampoco se convierte este incidente operativo, con RAM fisica aun sobre 2 GiB, en un rechazo definitivo de calidad basado en 72 resultados inexistentes. El resumen distingue lo observado, la contabilidad faltante y las adjudicaciones pendientes.

## J. Fase 2 y decisiones pendientes

**Fase 2 NO desbloqueada y NO iniciada**: DEV-01 exige seleccion definitiva del LLM, no satisfecha. A/B/C, hipotesis H1/H2, integracion de produccion, FastAPI y frontend no se han ejecutado ni declarado terminados.

Lo pendiente no es otra ronda artificial de preparacion: hace falta disponibilidad estable de compromiso y una decision expresa del responsable sobre el experimento interrumpido. No se reinicia S15 o el lote automaticamente. Si se continuaran solo los 68 pendientes, el intento fallido original seguiria contando; no podria recuperarse 100% de JSON/utilizabilidad mediante un reintento oculto. Si se cambia prompt/modelo/protocolo tras haber visto reserva, se necesita una nueva justificacion y seleccion independiente. Un uso experimental de un candidato no aprobado requiere la desviacion metodologica expresa ya prevista, que aqui no se concede.

Para la evaluacion A/B/C definitiva siguen pendientes familias nuevas independientes del piloto, particiones y ground truth registrados, congelacion de componentes/prompts, adjudicacion de evidencias, control de presupuestos de contexto y presentacion exploratoria por familias. No se reutiliza este piloto como demostracion de H1/H2 ni como conjunto independiente final.

## K. Git, archivos y comprobaciones finales

Todo permanece en **develop**, local y sin staging; no se ejecutaron add, commit, push, merge, rebase, reset o clean. README y roadmap reflejan seleccion inconclusa/Fase 2 bloqueada. Los unicos cambios tracked previstos son esos dos estados documentales; motores, esquema, taxonomia, muestras e historicos previos conservan sus bytes.

Se implementaron los seis modulos runtime y sus pruebas, registro de aprobacion global/binding, ocho archivos de congelacion, prompt r1, recibos/metricas/tabla de resultados y esta acta. Se actualizaron protocolo/compatibilidad/verificacion y avisos de estado de las fichas; las vistas originales no se convirtieron en revisiones individuales ficticias. El inventario final del cierre identifica exactamente los archivos creados/modificados y hashes.

Antes de seleccion pasaron **731 pruebas** y la comparacion de 72 artefactos. Las comprobaciones finales posteriores al incidente se registran en el recibo final de verificacion: suite de regresion, integridad del dataset y referencias, congelaciones, payloads, fuente del modelo/digest, historico v1/1A/1B, Git, enlaces e inventario. Las pruebas Python no son benchmarks ni adjudicacion humana. **Pasada final: 731 aprobadas, cero fallidas/omitidas, en 4,55 s** (488 regresiones anteriores y 243 del piloto v2). El [inventario exacto del cierre](../experiments/results/pilot_v2/pilot-v2_20261102T194623Z/closure_inventory.json) distingue archivos preexistentes y cambios de esta instruccion; `final_verification.json` registra las comprobaciones e integra el hash de ese inventario.
