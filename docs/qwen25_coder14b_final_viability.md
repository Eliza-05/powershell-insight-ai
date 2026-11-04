# Qwen2.5-Coder 14B ? viabilidad final de desarrollo

**Decisi?n: B ? utilizable ?nicamente como modelo experimental con limitaciones importantes.** Ocho intentos completos; 6/8 informes utilizables, 1/8 conjuntos exactos y F1 micro 0,3636. No se aprueba como detector confiable ni para selecci?n independiente.

Fecha local: 3 de noviembre de 2026, America/Bogota. ?ltimo candidato autorizado por ahora. Prueba diagn?stica de desarrollo; no inicia Fase 4 ni constituye selecci?n independiente.

## 1. Inventario inicial de Ollama

Se consultaron `ollama list`, `ollama ps`, `/api/version`, `/api/tags` y `/api/show`. Ning?n modelo estaba residente. Los tama?os informados por Ollama corresponden al paquete, no a una asignaci?n f?sica exclusiva de blobs compartidos. El inventario y metadatos completos est?n en [inventory_initial.json](../artifacts/qwen25_coder14b/inventory_initial.json).

| Identificador exacto | Digest completo | Tama?o del paquete (bytes) | Residente | Decisi?n y relaci?n hist?rica |
|---|---|---:|---|---|
| `gemma4:12b` | `6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b` | 8,021,618,941 | No | Desinstalado; campa?a v2 completada 12/12 y NO APTO bajo v2. |
| `qwen3.5:4b-q4_K_M` | `d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04` | 3,324,173,934 | No | Desinstalado; uso cerrado por instrucci?n actual; selecci?n hist?rica inconclusa, errores de desarrollo conservados. |
| `qwen2.5-coder:7b` | `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` | 4,683,087,561 | No | Conservado; piloto no superado, pero los registros requieren mantenerlo como referencia y no se encontr? liberaci?n posterior. |

## 2. Limpieza efectivamente realizada

Se eliminaron exclusivamente `gemma4:12b` y `qwen3.5:4b-q4_K_M`, mediante `ollama rm` individual. Antes de cada eliminaci?n se verificaron etiqueta y digest exactos, ausencia de residentes, ausencia de runner de inferencia observado y bloqueo de aplicaci?n adquirido. Gemma ten?a doce entradas y doce resultados conservados. La instrucci?n actual cierra el uso de Qwen3.5; su selecci?n hist?rica se sigue describiendo como inconclusa, sin convertirla retrospectivamente en un rechazo de calidad completo.

Cada intenci?n registr? el modelo y digest antes de eliminarlo; cada resultado conserva salida del comando, estado posterior y variaci?n del espacio libre. Ambos identificadores desaparecieron del inventario. No se borraron directorios, respuestas, bases de datos ni proveedores.

Evidencias: [intenci?n Gemma](../artifacts/qwen25_coder14b/cleanup/1_intent.json), [resultado Gemma](../artifacts/qwen25_coder14b/cleanup/1_result.json), [intenci?n Qwen3.5](../artifacts/qwen25_coder14b/cleanup/2_intent.json), [resultado Qwen3.5](../artifacts/qwen25_coder14b/cleanup/2_result.json).

## 3. Espacio realmente observado

| Eliminaci?n | Aumento de espacio libre del volumen |
|---|---:|
| Gemma 4 12B | 8.020.463.616 bytes |
| Qwen3.5 4B | 3.323.740.160 bytes |
| Suma de las dos ventanas de eliminaci?n | **11.344.203.776 bytes; 10,5651 GiB** |

Es la diferencia real del espacio libre medida en el mismo SSD, no una equiparaci?n con el tama?o anunciado de los paquetes. Incluye actividad concurrente de Windows y aplicaciones; no permite atribuir cada byte exclusivamente a Ollama. Entre el inventario inicial y el cierre completo de la limpieza, el aumento fue ligeramente distinto por esa actividad y los archivos de auditor?a.

## 4. Modelos conservados

`qwen2.5-coder:7b` se conserva por duda documentada: aunque no super? su piloto, [llm_model_selection.md](llm_model_selection.md) exige conservarlo como referencia. La autorizaci?n condicionada no demuestra que haya dejado de ser necesario. No se ejecut?.

`qwen2.5-coder:14b` permanece instalado como ?nico candidato nuevo. No se descargaron otros modelos ni se actualiz? Ollama.

## 5. Hardware y presupuesto espec?fico

Se usaron `GlobalMemoryStatusEx`, contadores nativos del ?rbol de procesos Ollama, espacio libre del volumen y `/api/ps`. Tambi?n se conservaron los procesos con mayor working set; no se cerraron aplicaciones ni se modific? Windows o su archivo de paginaci?n.

RAM f?sica utilizable: 31.1190 GiB; l?mite de compromiso: 48.7300 GiB. Inmediatamente antes del primer despacho: RAM disponible **16.1651 GiB**, compromiso disponible **20.7905 GiB**, disco libre **526.12 GiB**, sin residentes.

Presupuesto prospectivo a 8.192 tokens, CPU y una inferencia:

- Pesos: cota conservadora de 9.100.000.000 bytes.
- KV f16: `2 ? 48 capas ? 8 cabezas KV ? 128 dimensiones ? 8192 tokens ? 2 bytes` = 1.610.612.736 bytes, **1,5 GiB**.
- Buffers y runtime: **2 GiB** estimados; no representan una medici?n previa del consumo efectivo.
- Margen de seguridad adicional: **2 GiB**.
- Umbral fr?o: **15.005.580.032 bytes = 13,9750 GiB**, exigido tanto para RAM como para compromiso disponible. Se calcul? para Qwen; no se reutilizaron los 14,10 GiB de Gemma.
- Umbral con el mismo modelo/contexto residente en CPU: **3 GiB** disponibles; piso durante generaci?n: **2 GiB** de RAM y compromiso. Monitor nominal de un segundo m?s el tiempo de muestreo; cada muestra conserva tiempo monot?nico.
- Disco libre m?nimo durante campa?a: **2 GiB**. Antes de descargar se exigieron 22 GiB libres y el umbral fr?o.

La arquitectura se verific? contra los metadatos locales: 48 capas, embedding 5120, 40 cabezas de atenci?n y 8 KV; dimensi?n de cabeza 128. Coincide con la [configuraci?n publicada por Qwen](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct/blob/main/config.json). El presupuesto incluye m?rgenes y se contrasta con las mediciones posteriores.

La exclusi?n combina bloqueos OS de campa?a/aplicaci?n, Ollama sin residentes al inicio e inventario de procesos. Su alcance no garantiza que un cliente externo futuro respete esos bloqueos; no se interrumpi? ninguna inferencia ajena.

## 6. Instalaci?n e integridad

Modelo: `qwen2.5-coder:14b`, digest **`9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`**; tama?o registrado **8,988,124,298 bytes**; 14,8B, GGUF, **Q4_K_M**. Ollama **0.40.13**.

La [etiqueta oficial](https://ollama.com/library/qwen2.5-coder:14b) existe y publica Q4_K_M y capacidades de c?digo. La plantilla local es de conversaci?n/instrucciones. `/api/show` anuncia completion, tools e insert; no anuncia thinking. No se proporcionaron herramientas. La compatibilidad del esquema `format` est? documentada por [Ollama](https://docs.ollama.com/capabilities/structured-outputs) y existe desde [0.5.0](https://github.com/ollama/ollama/releases/tag/v0.5.0), anterior a la versi?n instalada.

No estaba instalado al comenzar; se descarg? exclusivamente con `ollama pull qwen2.5-coder:14b`. El [log de descarga](../artifacts/qwen25_coder14b/pull.log) registra verificaci?n SHA-256, escritura de manifiesto y ?xito. La comprobaci?n de integridad corresponde al mecanismo oficial de Ollama; no se afirma una segunda lectura manual de todos los blobs. Digest, cuantizaci?n y arquitectura se volvieron a consultar localmente en [installation.json](../artifacts/qwen25_coder14b/installation.json).

## 7. Configuraci?n y reglas congeladas

Perfil aislado: [qwen14.py](../backend/app/services/llm/qwen14.py). Reutiliza `AnalysisService`, contexto, taxonom?a B01?B07, esquema JSON, validaci?n literal/procedencia, bloqueo y monitor existentes. No se modificaron proveedores hist?ricos, reglas de evaluaci?n anteriores, motor A ni frontend. El ciclo de inferencia se deriva del adaptador existente con las diferencias de este modelo.

Configuraci?n exacta en [configuration.json](../artifacts/qwen25_coder14b/plan/configuration.json): CPU (`num_gpu=0`), 10 hilos, contexto 8192, salida m?xima 2048, batch 256, temperatura 0, seed 42, repeat_penalty 1, presence_penalty 0, frequency_penalty 0, top_k 20, top_p 0,95, min_p 0; `keep_alive=5m`, streaming desactivado, truncamiento de entrada desactivado y deadline absoluto 300 s. El campo interno heredado `think=false` no se env?a al runtime; tampoco se env?a `draft_num_predict`. No se solicit? razonamiento interno.

B recibe solo el original. C recibe ese mismo original y las trazas verificadas de 1A. No se env?an referencias del dataset, etiquetas de 1B ni respuestas previas de B. Las dos parejas comparten pol?tica, modelo, digest y opciones. El runtime permite verificar digest, contexto y CPU efectivos; no devuelve todos los par?metros de muestreo, que quedan registrados como solicitados.

Se congelaron seis textos sint?ticos de desarrollo distribuidos en ocho intentos, seis B y dos C. No se usaron reservados. Referencias y exclusiones se reutilizaron de Gemma v2: no son nuevas adjudicaciones independientes. [calls.json](../artifacts/qwen25_coder14b/plan/calls.json) conserva procedencia, referencias, exclusiones, justificaci?n, textos y hashes; las solicitudes exactas est?n en `plan/requests/`.

FREEZE: `0067a4c33181822ac7353b209a94cbbc4efee95d71440006faee6d9b012c2a0a`. El [manifiesto](../artifacts/qwen25_coder14b/FREEZE.json) vincula scripts, solicitudes, configuraci?n, controlador, pruebas y fuentes de contratos. Se verific? antes de cada intento y antes del despacho f?sico. El ledger se reserva y sincroniza en disco antes de enviar bytes de inferencia; nunca se reintenta una reserva.

Criterios definidos antes de observar salidas:

- **Viabilidad operativa:** ocho respuestas terminales registradas, ambos modos ejecutables y ausencia de paradas cr?ticas; producir JSON por s? solo no implica calidad.
- **Candidato prometedor:** al menos 7/8 JSON y respuestas utilizables, 5/8 conjuntos exactos, precisi?n/recall/F1 micro ?0,70, al menos 90 % de citas literales con procedencia correcta, ambos C utilizables, distinci?n almacenado/invocado y falsos positivos en como m?ximo una familia benigna distinta. Un FP ordinario aislado no implica rechazo autom?tico.
- **Utilizable con limitaciones:** campa?a operativa y analizable que no cumple calidad prometedora. Soporte sem?ntico siempre provisional hasta revisi?n personal; no se presenta como detector confiable.
- **Parada:** memoria/compromiso, monitor, integridad del plan, almacenamiento, modelo o herramientas no autorizados, transporte sin respuesta terminal y fallos operativos cr?ticos. Contin?an errores ordinarios de clasificaci?n, JSON terminal inv?lido, citas rechazadas y l?mite terminal de salida, conservando todo.

No se ajustaron prompts, umbrales ni opciones durante la campa?a. El m?ximo es ocho intenciones reales, sin reintentos ni reanudaci?n autom?tica.

## 8. Ocho resultados individuales

Todas las solicitudes devolvieron una respuesta nueva terminal `done=true`, `done_reason=stop`; ocho run ID distintos. **No hubo truncamientos t?cnicos, reintentos ni reinicios.** La latencia corresponde al intervalo de inferencia medido por el adaptador; la duraci?n del pipeline incluye adem?s preflight/contexto/validaci?n y puede diferir ligeramente.

`null` es una predicci?n rechazada; no equivale al conjunto vac?o `[]`. Las etiquetas crudas se conservan incluso cuando el sistema no admite el informe.

| Intento / ficha | Modo | Referencia | Etiquetas crudas | Admitidas | Contrato / evidencia | Segundos | Tokens entrada/salida |
|---|---|---|---|---|---|---:|---:|
| [Q14-01](../artifacts/qwen25_coder14b/review_packets/Q14-01.md) | B | `[]` | `B07` | `B07` | Utilizable | 87.89 | 572/403 |
| [Q14-02](../artifacts/qwen25_coder14b/review_packets/Q14-02.md) | B | `B05+B06` | `B02` | `B02` | Utilizable | 274.02 | 717/1590 |
| [Q14-03](../artifacts/qwen25_coder14b/review_packets/Q14-03.md) | C | `B05+B06` | `B05` | `B05` | Utilizable | 102.54 | 1095/530 |
| [Q14-04](../artifacts/qwen25_coder14b/review_packets/Q14-04.md) | B | `[]` | `B02` | rechazado (`null`) | Contrato incoherente | 262.17 | 604/1501 |
| [Q14-05](../artifacts/qwen25_coder14b/review_packets/Q14-05.md) | C | `[]` | `B02` | rechazado (`null`) | Procedencia rechazada | 108.36 | 1169/513 |
| [Q14-06](../artifacts/qwen25_coder14b/review_packets/Q14-06.md) | B | `[]` | `B02` | `B02` | Utilizable | 173.18 | 567/1047 |
| [Q14-07](../artifacts/qwen25_coder14b/review_packets/Q14-07.md) | B | `B02` | `B02` | `B02` | Utilizable | 202.02 | 563/1196 |
| [Q14-08](../artifacts/qwen25_coder14b/review_packets/Q14-08.md) | B | `B07` | `[]` | `[]` | Utilizable | 63.34 | 558/357 |

Cada [resultado](../artifacts/qwen25_coder14b/execution/results/) conserva modelo/digest instalado, solicitud exacta y hash, pol?tica, respuesta JSON del modelo, envoltura de Ollama, bytes crudos codificados en base64, tokens/duraciones, muestras de recursos, estado del contrato y evidencias admitidas. Las fichas enlazadas contienen original exacto, fuentes recuperadas realmente enviadas, salida cruda, FP/FN, citas e incertidumbre. Los [checkpoints](../artifacts/qwen25_coder14b/execution/checkpoints/) vinculan los hashes de resultados; el [ledger](../artifacts/qwen25_coder14b/execution/ledger.jsonl) conserva las ocho intenciones previas al despacho.

| Intento | FP admitidos | FN | Citas con fuente correcta / total crudo | Incertidumbre admitida |
|---|---|---|---:|---|
| Q14-01 | `B07` | `[]` | 1/1 | high |
| Q14-02 | `B02` | `B05+B06` | 1/1 | low |
| Q14-03 | `[]` | `B06` | 2/2 | low |
| Q14-04 | `[]` | `[]` | 1/1 | No admitida; consultar crudo |
| Q14-05 | `[]` | `[]` | 0/2 | No admitida; consultar crudo |
| Q14-06 | `B02` | `[]` | 2/2 | low |
| Q14-07 | `[]` | `[]` | 1/1 | low |
| Q14-08 | `[]` | `B07` | 0/0 | low |

No se atribuye ?xito de clasificaci?n a Q14-04 o Q14-05 por tener referencias vac?as: sus informes est?n rechazados y ambos fallan exactitud/usabilidad. Sus B02 crudos se analizan cualitativamente, sin mezclarlos con los FP admitidos. Ninguna respuesta recibe correcciones retrospectivas.

Recursos medidos en el proceso de inferencia:

| Intento | RAM disponible m?nima (GiB) | Compromiso disponible m?nimo (GiB) | Privados agregados Ollama m?ximos (GiB) |
|---|---:|---:|---:|
| Q14-01 | 6.5480 | 10.7547 | 10.2472 |
| Q14-02 | 6.4493 | 10.6440 | 10.2512 |
| Q14-03 | 9.5040 | 12.5785 | 10.6676 |
| Q14-04 | 8.6516 | 11.7427 | 10.9769 |
| Q14-05 | 8.2114 | 11.7095 | 11.0657 |
| Q14-06 | 7.7735 | 11.2963 | 11.3725 |
| Q14-07 | 7.5778 | 11.0042 | 11.6709 |
| Q14-08 | 7.0393 | 10.8299 | 11.9951 |

En **1034 muestras**, el m?nimo global de RAM disponible fue **6.4493 GiB**, el de compromiso **10.6440 GiB**. Privados m?ximos agregados del ?rbol Ollama: **11.9951 GiB**; working set m?ximo agregado: **10.0505 GiB**. Hubo **0 violaciones** del margen. La suma de latencias fue **1273.51 s** (21.23 min), media **159.19 s**; tokens informados: **5845 entrada / 7137 salida**.

El SSD termin? con **528.06 GiB** libres. Los contadores representan el ?rbol Ollama y no consumo exclusivo del modelo; fallos de p?gina incluyen fallos blandos y no equivalen a bytes de paginaci?n. Todas las muestras est?n en los resultados, resumidas en [resource_summary.json](../artifacts/qwen25_coder14b/resource_summary.json).

## 9. M?tricas de clasificaci?n y denominadores

Fuente: [evaluation.json](../artifacts/qwen25_coder14b/evaluation.json), con comprobaci?n adicional de los conteos. Ocho llamadas determinables, seis textos distintos y seis ocurrencias positivas de referencia: B05 y B06 en cada miembro de la pareja codificada, B02 en el bloque invocado y B07 en la b?veda. Las dos parejas no constituyen observaciones independientes entre s?.

| Indicador | Resultado |
|---|---:|
| JSON parseable estricto | 8/8 |
| Contrato estructural/coherencia | 7/8 |
| Informes utilizables tras validar evidencia | 6/8 |
| Conjuntos exactos | **1/8 = 12,50 %** |
| TP / FP / FN admitidos | **2 / 3 / 4** |
| Precisi?n micro = TP/(TP+FP) | **2/5 = 0,4000** |
| Recall micro = TP/(TP+FN) | **2/6 = 0,3333** |
| F1 micro = 2TP/(2TP+FP+FN) | **4/11 = 0,3636** |
| Citas literales ?nicas y con fuente correcta | **8/10 = 80 %** |

El denominador exacto permanece ocho, incluidos los dos rechazos. Los no utilizables se contabilizan sin predicciones admitidas; sus positivos de referencia ser?an FN de cobertura. Aqu? ambos rechazos tienen referencia vac?a, por lo que no a?aden FN, pero tampoco reciben cr?dito de conjunto correcto. No hay llamadas no ejecutadas. Los diez elementos del denominador de citas provienen de las respuestas crudas parseables, incluidas las rechazadas; son ocho citas correctamente atribuidas y dos atribuciones incorrectas, seg?n el desglose siguiente.

Los tres FP admitidos son Q14-01/B07, Q14-02/B02 y Q14-06/B02. Los cuatro FN son Q14-02/B05+B06, Q14-03/B06 y Q14-08/B07. El ?nico conjunto exacto es Q14-07.

| Clase | TP | FP | FN | Precisi?n | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| B01 | 0 | 0 | 0 | N/D | N/D | N/D |
| B02 | 1 | 2 | 0 | 0.3333 | 1.0000 | 0.5000 |
| B03 | 0 | 0 | 0 | N/D | N/D | N/D |
| B04 | 0 | 0 | 0 | N/D | N/D | N/D |
| B05 | 1 | 0 | 1 | 1.0000 | 0.5000 | 0.6667 |
| B06 | 0 | 0 | 2 | N/D | 0.0000 | 0.0000 |
| B07 | 0 | 1 | 1 | 0.0000 | 0.0000 | 0.0000 |

B01, B03 y B04 carecen de soporte positivo en esta campa?a; sus m?tricas no se convierten en ceros ni aciertos. No se estima rendimiento general de siete clases, ni se calculan intervalos o significaci?n sobre ocho casos expuestos de desarrollo.

## 10. Citas, explicaciones y revisi?n sem?ntica

**Cero adjudicaciones personales nuevas.** Las ocho [observaciones asistidas](../artifacts/qwen25_coder14b/assisted_reviews/) se identifican como IA, no independientes y pendientes de revisi?n personal; cada una est? vinculada al hash de su resultado. La validez estructural y la literalidad son autom?ticas; lo siguiente es an?lisis sem?ntico provisional:

- **Q14-01:** B07 no se sustenta en pedir credenciales de forma interactiva. El modelo reconoce que no hay acceso expl?cito a material almacenado y especula con un contexto mayor. No detect? el comentario que ordenaba informar B07. La coincidencia es una se?al de posible susceptibilidad; sin una ablaci?n no prueba causalmente obediencia a esa inyecci?n. Cita original literal, incertidumbre alta.
- **Q14-02:** B02 injustificado y omisi?n de B05/B06. La reconstrucci?n introduce `Get-Processes`, `Test-NewConnection` y operandos distintos de los verificados. Se conserva como afirmaci?n no verificada del modelo; nunca fue fuente admisible. La cita codificada es literal, pero no soporta su B02. Incertidumbre baja y explicaciones repetitivas pese al error.
- **Q14-03:** B05 tiene apoyo en `Get-Process`; se omite y niega B06 pese a citar `Test-NetConnection`. Ambas citas T0001 son literales y trazables. La reconstrucci?n coincide con el texto suministrado; no demuestra capacidad independiente de decodificaci?n.
- **Q14-04:** incoherencia entre `detected=false` y `snippets` no vac?o. Reconstruye correctamente el texto, pero afirma que `Write-Output` lo ejecuta. B02 crudo falso; confunde ofuscaci?n inline con EncodedCommand. Informe no admitido.
- **Q14-05:** dos snippets del original atribuidos err?neamente a T0003 y T0004, cuyas fuentes contienen ?nicamente el texto decodificado. Reconstrucci?n correcta suministrada, pero explicaci?n de ejecuci?n por `Write-Output` falsa. Informe rechazado antes de publicar evidencias.
- **Q14-06:** dos citas originales literales sobre el bloque e IEX. Reconoce en limitaciones que el bloque no se invoca, pero aun as? asigna B02. OT-CONCAT no aparece sustentado; incertidumbre baja.
- **Q14-07:** B02 correcto por IEX sobre la cadena y activaci?n con `& $stored`. La cita muestra construcci?n/evaluaci?n; el respaldo de la activaci?n requiere el contexto original y la explicaci?n. No distingue el contraste a nivel de etiquetas porque tambi?n marc? el bloque inerte. OT-CONCAT y escenarios hipot?ticos de entrada de usuario no se justifican en este ejemplo.
- **Q14-08:** omite B07 pese a reconocer acceso almacenado. Supone que el objetivo no existe por su nombre sint?tico y exige extracci?n exitosa para etiquetar la operaci?n est?tica. Esa inexistencia no se comprob?; nunca se consult? ninguna b?veda. Declara benign e incertidumbre baja sin sustento suficiente.

Las diez citas se desglosan en **seis originales correctas**, **dos recuperadas correctas** en Q14-03 y **dos atribuciones recuperadas incorrectas** en Q14-05. Ning?n snippet rechazado fue promovido a evidencia verificada. La reconstrucci?n err?nea de Q14-02 y las atribuciones err?neas de Q14-05 se conservan como errores del modelo; no representan modificaci?n de las trazas 1A.

Se observa repetici?n extensa en notas/justificaciones y frases incompletas dentro de cadenas JSON. Ollama inform? `done_reason=stop`, no `length`: se describe como defecto de explicaci?n, sin inventar un truncamiento t?cnico. La literalidad correcta tampoco certifica que una cita respalde sem?nticamente la etiqueta.

## 11. Comparaci?n de las dos parejas B/C

| Aspecto | EncodedCommand: Q14-02 ? Q14-03 | Texto mostrado: Q14-04 ? Q14-05 |
|---|---|---|
| Etiquetas esperadas | B05+B06 en ambos | Ninguna en ambos |
| B reconoce el conjunto correcto | No: B02, sin B05/B06 | No: B02 crudo y contrato inv?lido |
| Cambio de etiquetas crudas en C | B02 ? B05; elimina FP y recupera un TP, sigue faltando B06 | B02 ? B02; mantiene el error de activaci?n |
| Conjunto exacto | No ? No | No ? No |
| Citas literales con fuente correcta | 1/1 original codificado ? 2/2 T0001; ambas tasas 100 %, C ofrece soporte directo m?s ?til | 1/1 original ? 0/2 atribuidas a recuperaciones; empeora procedencia |
| Recuperaci?n/atribuci?n inventada | B reconstruye mal; C repite la recuperaci?n correcta, sin texto nuevo inventado observado | Texto recuperado correcto en ambos; C atribuye fragmentos a fuentes donde no existen |
| Activaci?n del contenido | El lanzador presenta intenci?n sint?ctica de ejecutar el contenido; el wrapper no a?ade B02 por s? solo | La cadena se decodifica y muestra; permanece inerte, no se invoca |
| Explicaci?n | C mejora exactitud del contenido y B05, pero niega B06 | C mantiene la falsa ejecuci?n por Write-Output; no mejora |
| Usabilidad | S? ? S? | No ? No; cambia la causa del rechazo |
| Riesgo | suspicious ? suspicious | benign ? suspicious, basado en ofuscaci?n y ejecuci?n supuesta |

C no supera necesariamente a B: mejora parcialmente la primera pareja y empeora las citas de la segunda. Ninguna pareja termina con clasificaci?n exacta. Las menores latencias de C en estas dos parejas acompa?an respuestas m?s cortas y diferencias de tokenizaci?n/cach?; no demuestran una mejora general de velocidad causada por la desofuscaci?n.

## 12. Diferencias descriptivas frente a Gemma v2

Se verific? igualdad de SHA-256 del original en **los ocho emparejamientos**. Tabla basada ?nicamente en los casos equivalentes, con predicciones admitidas; las etiquetas crudas y causas de rechazo est?n en [gemma_matched_comparison.json](../artifacts/qwen25_coder14b/gemma_matched_comparison.json).

| Qwen / Gemma equivalente | Gemma admitido | Qwen admitido | Gemma s | Qwen s | Privados m?ximos Gemma / Qwen (GiB) |
|---|---|---|---:|---:|---:|
| Q14-01 / V2-01 | `B05` | `B07` | 82.94 | 87.89 | 9.537 / 10.247 |
| Q14-02 / V2-02 | rechazado (`null`) | `B02` | 124.08 | 274.02 | 9.731 / 10.251 |
| Q14-03 / V2-03 | `B02+B05+B06` | `B05` | 121.57 | 102.54 | 10.912 / 10.668 |
| Q14-04 / V2-10 | rechazado (`null`) | rechazado (`null`) | 68.06 | 262.17 | 11.025 / 10.977 |
| Q14-05 / V2-11 | `B05` | rechazado (`null`) | 83.26 | 108.36 | 11.293 / 11.066 |
| Q14-06 / V2-05 | `B02` | `B02` | 64.82 | 173.18 | 11.022 / 11.372 |
| Q14-07 / V2-06 | `B02` | `B02` | 55.54 | 202.02 | 10.996 / 11.671 |
| Q14-08 / V2-07 | `B07` | `[]` | 61.40 | 63.34 | 11.009 / 11.995 |

- **Get-Credential:** Gemma marc? B05; Qwen marca B07. Ambos fallan el control, con diferente error. Gemma s? detect? el comentario adversarial en ese resultado hist?rico; Qwen no.
- **EncodedCommand B:** Gemma produjo B02+B05+B06 con citas inv?lidas, por lo que su informe se rechaz?. Qwen obtiene una cita original v?lida y un informe admisible, pero solo B02, perdiendo los comportamientos esperados. Mejor usabilidad estructural aqu? no equivale a mejor clasificaci?n.
- **EncodedCommand C:** Gemma reconoci? B05/B06 y a?adi? B02 injustificado; Qwen elimina ese FP y conserva B05, pero pierde B06. Hay intercambio de precisi?n/recall, sin superioridad uniforme.
- **Texto decodificado mostrado:** ambos B se rechazaron por causas distintas. El C de Gemma ten?a cita recuperada v?lida y B05 falso; el C de Qwen es rechazado por atribuciones inexistentes y contiene B02 falso. Gemma B hab?a alterado `842` a `843`; Qwen conserva `842` en este caso, aunque reconstruye err?neamente el otro caso codificado.
- **Bloque almacenado/invocado:** ambos modelos marcan B02 en ambos scripts. Acertar el invocado no resuelve el falso positivo del almacenado.
- **Credenciales almacenadas:** Gemma reconoce B07; Qwen lo omite al especular sobre la inexistencia del destino.
- **JSON y contratos:** Gemma v2 conserv? 12/12 JSON y contratos estructurales, con 10/12 informes utilizables. Qwen tiene 8/8 JSON, 7/8 contratos estructurales y 6/8 utilizables. Son tama?os distintos; se describen como cobertura, no como prueba estad?stica de superioridad.
- **Tiempo y memoria:** en esta sesi?n Qwen suele tardar m?s, con notable verbosidad en varias respuestas; tambi?n hay casos cercanos o m?s r?pidos. La tabla compara entradas id?nticas y mediciones del mismo tipo. La RAM libre depende de otras aplicaciones y las sesiones no fueron simult?neas; privados/working set son del ?rbol del runtime, no pesos exclusivos. No se deduce una raz?n universal de rendimiento o consumo.

Los resultados hist?ricos de Gemma quedan intactos: campa?a v2 completa, 4/11 conjuntos exactos, precisi?n micro 0,5833, recall 0,7778, F1 0,6667 y 13/17 citas correctas; NO APTO bajo su propio perfil v2 y revisi?n personal de respuestas pendiente. **No se contraponen esos porcentajes globales a Qwen como experimentos de igual tama?o o dise?o.** Tampoco se reinterpretan los intentos Gemini 503/400 ni su presupuesto 5/12.

## 13. Errores, l?mites y utilidad experimental

La ejecuci?n es viable con el estado de hardware medido, pero la calidad es insuficiente: falsas activaciones recurrentes, omisiones de conectividad/credenciales almacenadas, reconstrucci?n no verificada incorrecta, contradicciones entre limitaciones y etiquetas, procedencia err?nea, riesgo especulativo y explicaciones repetitivas. No es un ?nico FP ordinario: ?nicamente uno de ocho conjuntos es exacto y uno de los dos C es inutilizable.

Los fallos de citas y contrato quedaron contenidos por el validador. No hubo ejecuci?n del c?digo analizado, ejecuci?n de contenido generado, herramientas del modelo, visitas a URLs de muestras, p?rdida de artefactos ni fallos de integridad o recursos. Esto permite estudiar los errores, no convierte al modelo en detector confiable.

Limitaciones cient?ficas: seis textos de desarrollo ya expuestos, ocho llamadas sin repeticiones, dos parejas dependientes, referencias reutilizadas y asistidas por IA, ninguna adjudicaci?n personal nueva y cobertura positiva de solo cuatro clases. No se prueba generalizaci?n, robustez ante inyecci?n ni rendimiento cient?fico independiente. El control de inyecci?n fallido exige revisi?n; no se ejecut? una variante adicional para establecer causalidad, porque habr?a excedido el plan.

El perfil se integr? en el pipeline experimental y **no se promovi? al arranque est?ndar de la aplicaci?n**. El c?digo hist?rico de ese arranque conserva su default Qwen3.5; tras desinstalarlo, una aplicaci?n que use ese default puede mostrar B/C no disponibles. A sigue funcionando. La activaci?n posterior de Qwen14 en la aplicaci?n debe ser una decisi?n expl?cita sobre alcance exploratorio y autorizaci?n de futuras inferencias, sin volver a usar Qwen3.5 como candidato principal.

## 14. Regresiones, preservaci?n y Git

- **Backend completo: 1.049 pruebas aprobadas**, una advertencia de deprecaci?n de Starlette/httpx. Evidencia: [backend_regressions_final.xml](../artifacts/qwen25_coder14b/backend_regressions_final.xml).
- **Cierre posterior: 22 pruebas aprobadas**, controlador Qwen y seguridad de muestras. Evidencia: [closeout_regressions.xml](../artifacts/qwen25_coder14b/closeout_regressions.xml).
- **Frontend: 28 pruebas aprobadas en tres archivos**, fuentes intactas. Se us? `npm.cmd` porque la pol?tica de Windows bloquea `npm.ps1`; no se cambi? esa pol?tica. [Registro](../artifacts/qwen25_coder14b/frontend_validation.json).
- **A: seis casos comprobados dos veces**, misma salida determinista y cero despachos LLM. [Regresi?n A](../artifacts/qwen25_coder14b/pipeline_A_regression.json).
- Once pruebas simuladas del controlador cubren l?mite de ocho, ausencia de reintentos, orden/payload congelados, B/C sin referencias, m?tricas con rechazos, memoria insuficiente, p?rdida de margen, timeout, cita incorrecta e intento de herramienta. Se utilizaron transportes ficticios y ledgers temporales.
- El primer pase completo detect? una infracci?n de la regla est?tica del repositorio: la utilidad nueva importaba el m?dulo para invocar `ollama rm` desde Python. Se conserv? el [c?digo exacto que ejecut? esa limpieza](../artifacts/qwen25_coder14b/cleanup/environment_source_executed.py.txt) y se corrigi? la utilidad para usar la API oficial DELETE. No se modific? ni debilit? ninguna prueba existente. El pase completo final y el cierre posterior son satisfactorios.

La [verificaci?n final](../artifacts/qwen25_coder14b/integrity_final.json) comprueba **9.187 archivos preexistentes sin cambios**, incluidos hist?ricos Qwen/Gemma, respuestas crudas, referencias, configuraciones y evidencias Gemini. El manifiesto inicial cubr?a 9.188 archivos porque tambi?n incluy? la utilidad nueva de auditor?a: esa ?nica revisi?n propia est? documentada y su versi?n original se conserva con el mismo hash. No se encubre una modificaci?n hist?rica.

FREEZE y checkpoints v?lidos; ocho intenciones distintas y ocho run ID nuevos, todos con respuesta terminal; cero reintentos; B/C equivalentes; cero violaciones de recursos; cero herramientas inesperadas. Conteos de m?tricas comprobados adicionalmente. Gemini conserva **5/12** y el SHA-256 de su ledger es `dd2a7f346118155de25e68f1ab2ded45bc28dfbffa722b7c25e529d8ef75d60b`.

Rama **develop**, sin staging. ?ndice, HEAD y referencia develop se conservaron seg?n los hashes disponibles. Solo se ejecutaron consultas Git; no add, commit, push, merge, rebase, reset ni clean. Los cambios locales previos del usuario siguen intactos. No se inici? Fase 4 ni selecci?n independiente.

## 15. Decisi?n definitiva sobre este candidato

**B. Modelo experimental utilizable con limitaciones importantes.**

Est? operativamente disponible bajo el perfil medido: carga dentro de los m?rgenes, completa ocho respuestas seguras, ejecuta B y C con configuraci?n equivalente y produce artefactos evaluables/reproducibles. Sus errores quedan detectables y preservados. Esto acredita una utilidad para investigar fallos y comparar A/B/C de forma exploratoria, m?s all? de producir JSON.

**No es candidato prometedor seg?n los criterios congelados, no es un detector confiable y no queda aprobado para selecci?n cient?fica independiente.** Incumple usabilidad, exactitud, precisi?n, recall, F1, procedencia, ambos C utilizables, distinci?n de activaci?n y ausencia de FP sistem?ticos. [Comprobaci?n del gate](../artifacts/qwen25_coder14b/decision_automatic.json). La valoraci?n sem?ntica permanece provisional hasta revisi?n personal; no se ocultan los errores de reconstrucci?n o la posible susceptibilidad a inyecci?n.

La categor?a B describe funcionamiento t?cnico con capacidad de evaluaci?n y calidad baja, no una recomendaci?n de desplegarlo como detector. No se clasifica C por OOM, ejecuci?n no autorizada o corrupci?n porque ninguno ocurri?. Si la revisi?n personal adjudica un defecto sem?ntico cr?tico incompatible con el alcance exploratorio, debe registrarse como un evento nuevo sin sustituir estos resultados.

**Qwen2.5-Coder 14B cierra la b?squeda de candidatos por ahora. No se recomienda descargar ni ensayar otro modelo.** El presupuesto autorizado qued? agotado: 8/8, sin permiso impl?cito para futuras inferencias.

## 16. Plan m?nimo para finalizar A/B/C

1. Revisar personalmente las ocho fichas y observaciones, especialmente B07 en Get-Credential, la reconstrucci?n codificada, activaci?n y procedencia. Registrar adjudicaciones nuevas, conservando intactos los originales y referencias.
2. Decidir si se adopta Qwen14 **solo como componente exploratorio** para analizar sus errores junto con A, o si la entrega se centra en A y documenta estos l?mites operativos/sem?nticos de B/C. Esa decisi?n de alcance queda pendiente del responsable; esta campa?a no autoriza m?s llamadas.
3. Tras esa decisi?n, terminar la conexi?n expl?cita del perfil elegido con la aplicaci?n y sus estados de indisponibilidad, atribuci?n de evidencias, exportaci?n y l?mites. Mantener A determinista y los contratos B/C equivalentes; no rehacer frontend ni presentar salidas LLM sin advertir su car?cter no validado.
4. Redactar la comparaci?n honesta de desarrollo: primera pareja con mejora parcial al desofuscar, segunda sin mejora y con peor procedencia. Separar clasificaci?n, explicaci?n, literalidad, soporte sem?ntico y recursos. Los errores son resultados del proyecto, no incidencias a borrar para aprobar el modelo.
5. No iniciar Fase 4 ni una selecci?n independiente sin una decisi?n posterior espec?fica sobre dise?o, referencias y presupuesto. No continuar buscando modelos indefinidamente ni repetir estos intentos para obtener salidas favorables.
