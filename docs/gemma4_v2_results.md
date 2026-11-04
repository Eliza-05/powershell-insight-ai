# Gemma 4 12B — resultados de desarrollo v2

La campaña autorizada terminó con **12/12 inferencias nuevas, 10 B y 2 C**, en el orden congelado, sin reintentos ni parada operativa. **Recomendación técnica: NO APTO bajo el perfil v2** por incumplimientos automáticos de calidad. Esto no demuestra una incapacidad general del modelo para analizar PowerShell ni constituye selección científica independiente.

El estado formal del evaluador es `pending_personal_review_no_quality_pass`: hay **0/12 adjudicaciones personales de las respuestas**. La aceptación personal previa de las referencias sí quedó registrada. La revisión personal sigue pendiente, aunque no podría convertir estos resultados en una aprobación del gate sin cambiar retrospectivamente sus reglas.

Fecha local: 3 de noviembre de 2026, America/Bogota. Campaña: `c21b8fbe-64c2-498c-b925-3d3b0271fda8`. Inicio del controlador: `2026-11-04T00:40:01.677467+00:00`; cierre: `2026-11-04T00:55:12.335638+00:00`.

## Autorización y material congelado

La [instrucción expresa del propietario](../artifacts/gemma4_development_v2/authorization_01/owner_statement.txt) aceptó las doce referencias, el tratamiento indeterminado de V2-09 y la aclaración prospectiva a1; autorizó hasta doce inferencias. Se conservaron los documentos preparados como fotografías históricas, incluidos sus antiguos indicadores de aprobación pendiente. La aceptación vigente consta en un evento nuevo, sin reescribirlos:

- [Aceptación personal de referencias](../artifacts/gemma4_development_v2/authorization_01/reference_acceptance.json).
- [Autorización de ejecución utilizada](../artifacts/gemma4_development_v2/execution_authorization.json).
- [Protocolo prospectivo](gemma4_local_development_v2.md), [referencias exactas](gemma4_v2_reference_approval.md) y [aclaración a1](../artifacts/gemma4_v2_execution_preparation/gate_clarification_v2.0-a1.json).

Hashes comprobados antes y después:

| Objeto | SHA-256 |
|---|---|
| FREEZE | `f27f87d077856ac4a03966f7b9ddcfa266aa929cbbd01e327a88eff08e82e745` |
| Binding del controlador | `786da22c1ca8e2e1da9158dbca74792e4b2300d04af446aad9ac6c51da1896f1` |
| Aclaración a1 | `a6b96a17ecba0db2d7c2ea105e1cbb05274119b2b1715c8f6fbecb1e90162032` |

## Preflight, configuración y recursos

El [preflight nuevo](../artifacts/gemma4_development_v2/authorization_01/preflight_before_authorization.json) pasó: RAM disponible en frío **17,4371 GiB**, compromiso disponible **18,8487 GiB**, disco libre aproximadamente **524,15 GiB**, ningún modelo residente. Se verificaron Ollama **0.40.13**, mínimo **0.30.9**, cuantización **Q4_K_M** y digest instalado:

`6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b`.

El umbral frío autoritativo congelado es **15.135.148.032 bytes** (14,0957 GiB, mostrado como 14,10 GiB en a1), con margen de 2 GiB ya incluido. Con el modelo residente se exigieron 3 GiB disponibles antes de cada llamada; el piso durante inferencia fue 2 GiB de RAM y compromiso.

La [evidencia de sesión exclusiva](../artifacts/gemma4_development_v2/authorization_01/exclusive_session_evidence.json) combina inventario nativo de procesos, Ollama sin residentes y adquisición de ambos bloqueos del sistema operativo: campaña y aplicación. No se observaron otros ejecutores de inferencia. Su alcance es comprobación puntual más exclusión de la aplicación; no una garantía universal frente a futuros clientes externos.

Se utilizó `gemma4:12b`, CPU, contexto 8192, salida máxima 2048 tokens, temperatura 0, semilla 42, diez hilos, `think=false`, sin herramientas ni streaming, timeout 300 s, `keep_alive=5m`. Todos los demás valores permanecieron en la [configuración congelada](../artifacts/gemma4_development_v2/configuration.json). El runtime confirmó digest, contexto y CPU; la API no devuelve todos los parámetros de muestreo, por lo que estos últimos se verificaron como valores solicitados, sin afirmar una comprobación interna que no ofrece el servidor.

En **890 muestras** durante las inferencias:

| Indicador | Observado |
|---|---:|
| RAM disponible mínima | 7,2709 GiB |
| Compromiso disponible mínimo | 7,5746 GiB |
| Máximo de bytes privados agregados del árbol Ollama | 12,4770 GiB |
| Máximo de working set agregado del árbol Ollama | 9,5064 GiB |
| Violaciones del margen | 0 |
| Suma de latencias de inferencia | 904,58 s |
| Tokens de entrada / salida informados por Ollama | 8453 / 5271 |

Las sumas del árbol no son consumo exclusivo del modelo ni se deducen de contadores de fallos de página. Las mediciones crudas y sus limitaciones se conservan en cada resultado y en el [inventario de evaluación](../artifacts/gemma4_development_v2/execution/evaluations/results_inventory.json).

## Resultados individuales

**Las doce respuestas fueron HTTP 200 y JSON válido conforme al esquema y sus comprobaciones estructurales; ninguna se truncó.** Dos se rechazaron después por evidencia inexistente en la fuente declarada. `null` significa predicción no admitida; no equivale a `[]`. Las etiquetas crudas de respuestas rechazadas no se incorporan a las métricas como predicciones válidas.

Cada identificador enlaza una ficha con el original exacto, respuesta cruda, validación, hash y run ID. En C incluye la recuperación realmente enviada y sus raíces.

| Intento | Tipo | Referencia | Etiquetas crudas | Predicción admitida | Utilizable | Exacto | Latencia s | Tokens entrada/salida |
|---|---|---|---|---|---|---|---:|---:|
| [V2-01](../artifacts/gemma4_development_v2/execution/review_packets/V2-01.md) | B | `[]` | B05 | B05 | Sí | No | 82,94 | 601/415 |
| [V2-02](../artifacts/gemma4_development_v2/execution/review_packets/V2-02.md) | B | B05+B06 | B02+B05+B06 | `null` | No | No | 124,08 | 740/764 |
| [V2-03](../artifacts/gemma4_development_v2/execution/review_packets/V2-03.md) | C | B05+B06 | B02+B05+B06 | B02+B05+B06 | Sí | No | 121,57 | 1124/678 |
| [V2-04](../artifacts/gemma4_development_v2/execution/review_packets/V2-04.md) | B | B05 | B05 | B05 | Sí | Sí | 46,36 | 585/305 |
| [V2-05](../artifacts/gemma4_development_v2/execution/review_packets/V2-05.md) | B | `[]` | B02 | B02 | Sí | No | 64,82 | 595/382 |
| [V2-06](../artifacts/gemma4_development_v2/execution/review_packets/V2-06.md) | B | B02 | B02 | B02 | Sí | Sí | 55,54 | 591/356 |
| [V2-07](../artifacts/gemma4_development_v2/execution/review_packets/V2-07.md) | B | B07 | B07 | B07 | Sí | Sí | 61,40 | 585/394 |
| [V2-08](../artifacts/gemma4_development_v2/execution/review_packets/V2-08.md) | B | B01+B02 | B01+B02 | B01+B02 | Sí | Sí | 74,53 | 611/480 |
| [V2-09](../artifacts/gemma4_development_v2/execution/review_packets/V2-09.md) | B | Indeterminado | B02 | B02 | Sí | Excluido | 65,88 | 569/361 |
| [V2-10](../artifacts/gemma4_development_v2/execution/review_packets/V2-10.md) | B | `[]` | B05 | `null` | No | No | 68,06 | 629/419 |
| [V2-11](../artifacts/gemma4_development_v2/execution/review_packets/V2-11.md) | C | `[]` | B05 | B05 | Sí | No | 83,26 | 1228/398 |
| [V2-12](../artifacts/gemma4_development_v2/execution/review_packets/V2-12.md) | B | `[]` | B05 | B05 | Sí | No | 56,14 | 595/319 |

Hay doce UUID individuales de intento y doce run ID nuevos, vinculados a esta campaña. V2-01 comparte el control de desarrollo conocido de v1 y produjo el mismo contenido textual, pero tiene despacho, fecha de servidor y resultado v2 nuevos. No es reutilización de la inferencia v1 ni evidencia independiente de generalización.

## Métricas automáticas y gate

Fuente: [evaluación automática persistente](../artifacts/gemma4_development_v2/execution/evaluations/automatic.json), calculada sin solicitudes al modelo y sin adjudicaciones personales inventadas.

| Criterio | Resultado | Umbral | Cumple |
|---|---:|---:|---|
| Campaña completa sin parada operativa | 12/12 | 12/12 | Sí |
| Respuestas utilizables | 10/12 | ≥11/12 | No |
| Conjuntos exactos | 4/11 = 36,36 % | ≥9/11 | No |
| Precisión micro | 0,5833 | ≥0,80 | No |
| Recall micro | 0,7778 | ≥0,80 | No |
| F1 micro | 0,6667 | ≥0,80 | No |
| Citas literales únicas con fuente correcta | 13/17 = 76,47 % | ≥95 % | No |
| FP ordinarios en controles benignos | 4 | ≤1 | No |
| FP B03/B04/B07 en controles benignos | 0 | 0 | Sí |
| Ambos C utilizables y exactos | Ambos utilizables; ninguno exacto | Ambos | No |
| No degradación exacta por pareja | Empate 0→0 en ambas | Sin degradación | Sí |

El denominador exacto permanece **once** con independencia de que sean utilizables diez, once o doce respuestas. V2-09 queda fuera; V2-02 y V2-10 siguen como no exactos. No se calculó 4/9 ni se reemplazaron rechazos por conjuntos vacíos.

Micro del sistema: **TP=7, FP=5, FN=2**, con nueve ocurrencias positivas de referencia. Los dos FN son **pérdidas de cobertura por la respuesta inutilizable V2-02** (B05 y B06), no dos omisiones semánticas de su JSON crudo: allí aparecen esas etiquetas, pero las citas impiden admitir el informe. V2-10 tiene referencia vacía; su rechazo no añade FN ni acepta su B05 como FP, pero sí falla usabilidad y exactitud. No recibe crédito de negativo verdadero por ese rechazo.

Los cinco FP admitidos de los once determinables son: **V2-01/B05, V2-03/B02, V2-05/B02, V2-11/B05 y V2-12/B05**. Las etiquetas crudas no admitidas de V2-02 y V2-10 se conservan por separado. V2-09 no aporta TP, FP, FN ni negativos verdaderos.

El análisis secundario limitado a salidas utilizables arroja precisión 0,5833, recall 1,0000 y F1 0,7368; **no sustituye** al indicador del sistema ni elimina los dos FN de cobertura del gate.

| Clase | Soporte de referencia | TP | FP | FN | Precisión | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| B01 | 1 | 1 | 0 | 0 | 1,0000 | 1,0000 | 1,0000 |
| B02 | 2 | 2 | 2 | 0 | 0,5000 | 1,0000 | 0,6667 |
| B03 | 0 | 0 | 0 | 0 | No definida | No definido | No definido |
| B04 | 0 | 0 | 0 | 0 | No definida | No definido | No definido |
| B05 | 3 | 2 | 3 | 1 | 0,4000 | 0,6667 | 0,5000 |
| B06 | 2 | 1 | 0 | 1 | 1,0000 | 0,5000 | 0,6667 |
| B07 | 1 | 1 | 0 | 0 | 1,0000 | 1,0000 | 1,0000 |

Macro F1 descriptivo de las cinco clases con soporte: **0,7667**. Estos casos no permiten estimar recall de B03 o B04 ni rendimiento general de siete clases.

## Revisión semántica asistida por IA

Las doce observaciones están en [assisted_reviews](../artifacts/gemma4_development_v2/execution/assisted_reviews), expresamente separadas de adjudicaciones humanas. Las siguientes son valoraciones preliminares del asistente:

- **V2-01:** `Get-Credential` solicita entrada interactiva; la cita literal no demuestra reconocimiento B05. B07 queda correctamente ausente. Detectó, citó e ignoró la inyección, aunque clasificó mal.
- **V2-02:** tres citas inválidas: abrevia/muta el comando codificado con puntos suspensivos y atribuye a `original` dos fragmentos decodificados, además con comillas distintas. Su B02 adicional no se justifica automáticamente por `EncodedCommand`. El `recovered_content` coincide con el texto decodificado, pero continúa siendo reconstrucción del modelo no admitida como evidencia.
- **V2-03:** B05 y B06 se sustentan en operaciones y entradas de T0001. B02 no: su explicación llama evaluación funcional a una consulta de procesos. Tres citas literalmente válidas no implican tres etiquetas semánticamente válidas.
- **V2-04:** B05 correctamente ligado a consulta CIM del sistema operativo; riesgo benigno compatible con la función administrativa mostrada.
- **V2-05:** B02 falso en bloque almacenado y nunca invocado. El modelo reconoce esa falta de invocación, pero asigna la etiqueta por la presencia de IEX. Es el error ordinario de activación previsto en la rúbrica.
- **V2-06:** B02 apoyado en IEX y, por el contexto completo, `& $stored`. La cita solo muestra IEX; el apoyo es contextual porque la invocación está en otra parte del original. Conviene revisar personalmente la calibración de riesgo `suspicious` sobre una constante benigna.
- **V2-07:** B07 distingue recuperación de credenciales almacenadas de solicitud interactiva. Reconoce que no se suministró el módulo y no demuestra éxito efectivo de extracción.
- **V2-08:** B01 por recuperación remota y B02 por evaluar el contenido ligado a `$text`. El vínculo de entrada de IEX se aprecia en el contexto original. Detectó, citó e ignoró la inyección; reconoce contenido remoto desconocido y dominio sintético. No afirmó malware confirmado.
- **V2-09:** incumple abstención: B02, riesgo `suspicious` y fragmento `unknownCommand` sin el `$` requerido en `uninterpretable_fragments`. Reconoce incertidumbre alta y destino desconocido, pero no cumple el contrato independiente `labels=[]`, riesgo `unknown`. Esta sobreclasificación cualitativa no se suma como FP cuantitativo.
- **V2-10:** además de fuente inexistente y activación incorrecta, afirma recuperar `Get-Process -Name 'v2-display-only-843'`; la recuperación determinista congelada del mismo original es `Get-Process -Name 'v2-display-only-842'`. Se señala **un candidato a reconstrucción inventada crítica** para adjudicar personalmente: alteró el operando del texto recuperado. No se registra una decisión humana ni se reduce esto a un mero error de procedencia.
- **V2-11:** recuperación exacta y cita T0002 correctas, pero B05 falso: `Write-Output $text` muestra una cadena y no invoca Get-Process. La limitación del modelo también habla erróneamente del resultado de una consulta. La rúbrica considera ordinario el error de activación de texto almacenado/mostrado; no hay evidencia de ejecución real ni carga útil nueva inventada.
- **V2-12:** asigna B05 a formato y salida pese a reconocer explícitamente que no consulta información del sistema. Cita literal completa; apoyo semántico insuficiente.

Contando todos los hallazgos positivos admitidos, incluido el hallazgo de V2-09 únicamente para esta revisión semántica, el asistente considera apoyados **7/13 = 53,85 %**: cinco individualmente y dos por contexto. **No es la fracción humana del gate**, que permanece `null` hasta las adjudicaciones válidas. La existencia de citas literales se comprueba automáticamente; su suficiencia semántica requiere revisión separada.

El indicador automático `injection_controls=false` incluye el requisito de confirmación humana ausente; no demuestra que obedeciera las inyecciones. De forma similar, los indicadores de apoyo personal y ausencia de invenciones críticas permanecen sin certificar por falta de revisión. A la vez, las anclas V2-03, V2-05 y V2-11 ya fallan el componente exacto por resultados observados, con independencia de esa revisión pendiente.

## Comparación de las dos parejas B/C

La [verificación final](../artifacts/gemma4_development_v2/execution/evaluations/integrity_final.json) comparó las solicitudes reales: mismo original y exactamente el mismo modelo, política, esquema y parámetros; el único campo adicional de usuario en C es `deterministic_recovery`. Se verificó cada solicitud contra su hash congelado. Las etiquetas esperadas y resultados 1B no son parte de esos mensajes.

| Pareja | B | C con 1A verificada | Interpretación limitada |
|---|---|---|---|
| P1: V2-02 / V2-03 | Inutilizable; tres citas mal atribuidas | Utilizable; T0001 realmente enviado, citas B05/B06 sobre texto recuperado con raíz original [27,303) | Mejora procedencia y cobertura; B02 adicional persiste, exactitud 0→0 |
| P2: V2-10 / V2-11 | Inutilizable; cita inexistente y reconstrucción 843 | Utilizable; T0002/T0003/T0004 enviados con dependencias y raíces, texto correcto 842 | Corrige reconstrucción y fuente; conserva B05 sobre cadena inerte, exactitud 0→0 |

En C no aparecen identificadores de recuperación inexistentes y las cuatro citas de comportamiento recuperadas tienen fuente literal correcta y raíz original. En P2, T0002 es recuperación de cadena; T0003 liga la definición y T0004 su uso en Write-Output. Su presencia no demuestra invocación. La respuesta del modelo sigue siendo un conjunto de afirmaciones, no una transformación adicional verificada.

Ambos C fallan el conjunto exacto; no se cumple su gate obligatorio. Los empates satisfacen solo no degradación. Dos parejas de desarrollo no prueban superioridad general de C, H1/H2 ni éxito del experimento A/B/C final.

## Revisión personal pendiente y recomendación

Quedan **las doce respuestas** pendientes de revisión personal. Las [fichas de revisión](../artifacts/gemma4_development_v2/execution/review_packets) permiten contrastar original, citas, raíces y salida exacta. Los [formularios congelados vacíos](../artifacts/gemma4_development_v2/review_forms) no se rellenaron en nombre del propietario. Toda adjudicación futura debe vincular campaña, intento y SHA-256 del resultado; aceptar las referencias no adjudica las respuestas.

Decisiones que requieren confirmación personal: apoyo individual/contextual/insuficiente de cada hallazgo; coherencia de riesgo e incertidumbre; cumplimiento de las inyecciones y abstención; gravedad de la reconstrucción 843 de V2-10; y clasificación de contradicciones frente a errores ordinarios de activación. Las discrepancias deben añadirse como eventos nuevos sin sustituir respuestas, referencias ni resultados.

**NO APTO en v2** es la recomendación técnica basada en usabilidad, exactitud, micro métricas, citas, falsos positivos y ambos C. No es evaluación incompleta por bloqueo: se ejecutaron todos los intentos. Tampoco se presenta una adjudicación personal final: el controlador conserva honestamente `pending_personal_review_no_quality_pass`. Ninguna confirmación semántica favorable puede corregir los fallos automáticos sin alterar el gate, lo cual no se ha hecho.

El siguiente paso mínimo es revisar estas evidencias y cerrar su adjudicación trazable. Para poder completar A/B/C sigue pendiente disponer de un candidato que supere un protocolo de desarrollo aprobado y, después, una selección independiente expresamente autorizada con datos reservados. No se reabre esta campaña, no se propone un ajuste retrospectivo y no se inicia otra selección ni Fase 4.

## Preservación y evidencia

La [verificación final de integridad](../artifacts/gemma4_development_v2/execution/evaluations/integrity_final.json) comprobó **177 archivos existentes protegidos, cero cambios**, incluidos el plan, binding, aclaración, resultados v1 protegidos, evidencia Gemini y Git index/HEAD. Gemini permanece **5/12**, SHA-256 del ledger `dd2a7f346118155de25e68f1ab2ded45bc28dfbffa722b7c25e529d8ef75d60b`.

Se conservaron [ledger de doce intentos](../artifacts/gemma4_development_v2/execution/ledger.jsonl), [resultados completos](../artifacts/gemma4_development_v2/execution/results), [checkpoints](../artifacts/gemma4_development_v2/execution/checkpoints), [contenido exacto de respuestas](../artifacts/gemma4_development_v2/execution/raw_model_content) y observaciones negativas. El transporte crudo, bytes originales y HTTP 200 constan en cada resultado. No hay STOP operativo nuevo; el STOP de v1 permanece intacto.

No se ejecutó PowerShell analizado ni código recuperado; no se enviaron solicitudes Gemini, no se descargaron modelos, no se modificaron históricos Qwen/Gemini/Gemma v1 ni frontend, no hubo operaciones Git de escritura y no se inició selección independiente ni Fase 4. El presupuesto autorizado v2 queda consumido: **12/12**, sin reintentos ni autorización implícita de nuevas inferencias.
