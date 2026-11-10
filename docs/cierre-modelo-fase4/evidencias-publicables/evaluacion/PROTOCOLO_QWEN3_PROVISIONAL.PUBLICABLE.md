> Copia publicable derivada de un informe historico. Rutas operativas redactadas y enlaces ajustados; no es una nueva validacion, acta humana o autorizacion. La responsabilidad vigente de Karol consta en el plan.

# Propuesta científica Qwen3-Coder v2 — PROVISIONAL Y BLOQUEADA

Esta propuesta corresponde al código `7fc29f86d50298207a2a480ac3989be175ec9cb1`. No es un FREEZE ni una autorización. El preflight técnico pasó con observaciones y las 767 pruebas nativas pasaron; la preparación de solicitudes F4 se interrumpió una sola vez por `proposal_context_budget_exceeded`. Las referencias humanas siguen pendientes. No existe candidato completo compatible con `Proposal.seal`.

## Procedencia y continuidad

La asociación antigua con Qwen14 está en `artifacts/phase4_preparation/proposal/configuration.json` del repositorio histórico versionado y en `docs/phase4_protocol_proposed.md` y `docs/phase4_preparation_delivery.md`. La configuración antigua no declara el perfil v2; el manifiesto antiguo tampoco corresponde al código actual. Se conservan sin sustitución. En la copia nueva, el mismo nombre relativo de artifacts pertenece a un directorio nuevo e independiente; su preparación parcial tampoco sustituye los antecedentes.

Se mantienen las hipótesis de `docs/methodology.md`, taxonomía B01–B07, diseño pareado A/B/C, 16 textos, 14 conjuntos determinados y dos indeterminados, 8/8 estratos de recuperación, criterios semánticos estrictos/permisivos, presupuesto y tratamiento de fallos propuestos. Las 16 identidades de texto originales se comprobaron por SHA-256 contra la plantilla histórica: no se editó un caso. Las referencias siguen siendo propuestas de IA, no verdad terreno humana aceptada.

Cambian prospectivamente el modelo/digest, perfil, política, estrategia común, sanitizador, verificador y contabilidad Linux respecto de Qwen14, según la elección explícita del responsable y los commits publicados. No se heredan métricas, aprobaciones o autorizaciones exploratorias de Qwen14. Los documentos anteriores que describen Windows, reservas Qwen14 o política v1 son antecedentes, no la especificación efectiva de este candidato.

El corpus de independencia preparado reúne 567 entradas sintéticas previas mediante el recolector y el inventario previos a F4. Conserva procedencias y hashes; no copia respuestas, métricas, ledger o autorizaciones históricos. La preparación se interrumpió antes del audit de independencia de esta versión: **no se afirma un audit nuevo satisfactorio**. La novedad semántica y los bloques requieren revisión humana.

## Condiciones previstas

- A: 1A y reglas 1B deterministas, sin proveedor.
- B: original sometido al preprocesamiento común de v2, sin recuperación adicional.
- C: mismo original/preprocesamiento, más recuperación 1A verificada; sin etiquetas 1B, respuestas B, referencias o hipótesis en el request.
- Qwen3-Coder `qwen3-coder:30b`, digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`, perfil `qwen3coder-v2`.
- Estrategia `v2-deterministic-layers-2`; sanitizador `comment-blanking-v2-diagnostics`; verificador `evidence-check-v2-bounded`.
- Política normalizada SHA-256 `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081`.
- CPU, `num_gpu=0`, temperatura 0, semilla 42, contexto 8192, salida máxima 2048, diez hilos, timeout 300 s, cero reintentos. Las demás opciones exactas se conservan en `CONFIGURATION.PROVISIONAL.json`, extraídas del perfil nativo; no se hacen overrides para pasar la preparación.
- 16 A, 16 B y 16 C; máximo 32 intenciones LLM, hoy 0 autorizadas y 0 intentadas. Semillas previstas de orden 40716 y contrabalanceo 61407, A primero en cada unidad y ocho unidades B/C en cada orden. El archivo nuevo completo de orden no llegó a generarse; no se presenta uno inventado como congelado.

B/C tienen política, parámetros, esquema y postprocesamiento comunes. La equivalencia se verificó con fixtures de desarrollo y transportes simulados antes de incorporar F4. No se ejecutaron inferencias F4 ni se analizaron sus respuestas.

## Bloqueo de contexto

La guarda actual exige `suma(bytes UTF-8 de messages) + 512 + 2048 <= 8192`: quedan 5632 bytes para los mensajes. La preparación autorizada fue rechazada por esa guarda. Es una cota conservadora basada en bytes, no una medición del tokenizer o de la capacidad real del modelo. No ocurrió una llamada, timeout o respuesta inválida.

Se conservó el intento parcial y no se repitió. No se reconstruyeron los requests rechazados para depurar ni se adaptaron textos, política, sanitizador, verificador, contexto, salida o contabilidad usando F4. El contrato vigente no permite completar esta preparación. Resolverlo exige una decisión metodológica explícita; cualquier revisión debe registrar la exposición de estas entradas y valorar una reserva independiente, sin tratarla como calibración seguida de evaluación virgen sobre los mismos textos.

## H1 y predicciones originales/aceptadas

H1 conserva la diferencia `micro-F1(C) − micro-F1(B)` sobre los 14 IDs determinables fijados prospectivamente. TP/FP/FN y precisión/recall/F1 se calculan conforme a `experiments/phase4/metrics.py`; macro sobre clases con soporte positivo, métricas por clase y exactitud de conjuntos se mantienen separadas.

La predicción principal es la publicada por el pipeline tras su verificador. El crudo original del LLM se conserva, junto con las decisiones de mantener/descartar; una etiqueta cruda rechazada no se promueve a predicción aceptada. El efecto corresponde al pipeline y no constituye una estimación aislada de la precisión intrínseca del LLM.

Un resultado no utilizable conserva `predicted=null`; nunca se convierte en `[]` como predicción negativa válida. Sus positivos determinados cuentan como FN de cobertura y no recibe crédito de conjunto exacto. La comparación secundaria de parejas ambas utilizables muestra su selección y no sustituye la principal. A informa cobertura completa/parcial; un parcial vacío no certifica benignidad.

## H2 y evidencia

H2 conserva la diferencia C−B en el número de afirmaciones factuales no respaldadas por unidad, agregada por bloque, con alternativa C<B. Requiere inventarios humanos completos y deduplicados de todos los campos de cada salida cruda, incluso rechazada: comportamientos, explicaciones, reconstrucciones, atribución, riesgo, incertidumbre y limitaciones con contenido factual.

Son no respaldadas las categorías estrictas `insufficient` y `contradicted`; `individual` y `contextual_cited` requieren soporte semántico real. `unassessable`, salidas vacías/ilegibles o inventarios vacíos no producen un cero favorable. La fracción de afirmaciones no respaldadas y el contexto permisivo son secundarios. Las citas literales se cuentan sobre las citas de crudos parseables, también rechazados; su existencia no sustituye adjudicación semántica.

Sin las revisiones personales completas ligadas a hashes, H2 queda pendiente o no evaluable. Un descarte del verificador no prueba ausencia de comportamiento ni garantiza verdad de las demás afirmaciones.

## Fallos y denominadores

| Situación | Registro y continuación | Tratamiento científico previsto |
|---|---|---|
| `evidence_check_incoherent` con respuesta terminal íntegra | Conservar raw y diagnóstico; no publicar predicción; no reintentar. Rechazo ordinario si pasan las comprobaciones operativas | `null`, FN de cobertura para positivos determinados; conservar crudo para H2 humano |
| JSON terminal inválido | Conservar bytes y diagnóstico; no reparar mediante LLM; continuar solo si el controlador lo clasifica como ordinario | No utilizable en H1; H2 requiere inventario humano evaluable, nunca cero automático |
| Salida terminal por límite de longitud | Conservar raw, tokens y estado; distinguirla de respuesta no terminal | No asumir clasificación completa; aplicar usabilidad del pipeline y reportar faltantes |
| Timeout/no terminal, HTTP crítico o recurso fallido | Mantener 300 s, preservar duración/estado; consumir intento reservado y parar nuevos despachos según STOP/circuito | No repetir ni excluir. Campaña parcial: descripción de ejecutados y faltantes, sin contraste completo H1/H2 |
| Error antes de reserva | Registrar preflight/cause; no declarar llamada intentada inexistente | Separar de intentos reservados/posiblemente consumidos |
| Reserva persistida pero resultado ausente/estado incierto | Intención gastada, conservar ledger/marker; nunca repetir automáticamente | Conservar faltante y trazabilidad; no inventar salida |
| Referencias indeterminadas | Mantener ambos casos e incertidumbre/conocidos mínimos | Excluirlos solo de métricas de etiquetas conforme al protocolo; informar los 16 y la cobertura. No reinterpretarlos tras ver resultados |

Reportar por separado: 16 previstos, 14 determinados, dos indeterminados, A/B/C ejecutados, llamadas autorizadas/reservadas/exitosas, timeouts, proveedor, rechazos y resultados no evaluables. Las métricas descriptivas de una campaña incompleta usan sus filas observadas y denominadores explícitos; no se presentan 14 unidades evaluadas si faltan pasos. El evaluador impide contraste H1/H2 completo si la campaña no está completa.

Se conservan las sensibilidades condicionales por bloques, bootstrap pareado de 2000 remuestreos con semilla 40716 y ajuste Holm de las dos hipótesis como en el protocolo previo, pendientes de aprobación. No se agregan métricas o intervalos después de ver salidas ni existe aceptación automática de hipótesis.

## Recursos, almacenamiento y reanudación

La política Linux es `linux-resident-mode-aware-v1`, recolector `linux-proc-cgroup-v2-v2`, overcommit observado 0, reserva fría completa 23.968.709.120 bytes, caliente compatible 3 GiB, margen continuo 2 GiB y mínimo de disco 2 GiB. La admisión no reserva RAM ni garantiza generación exitosa o ausencia de OOM. Diez hilos sobre ocho vCPU pueden penalizar latencia; se conservan los parámetros.

El binding `linux-model-filesystem-binding-v1` vincula la ruta canónica registrada `<ALMACEN_MODELO>` con su ancestro `<ANCESTRO_VALIDADO>`, montaje, dispositivo y capacidad. Se comprobó el SHA-256 real del archivo de evidencia, también incluido en el paquete. Cada sondeo vuelve a medir el espacio y verifica el montaje; no cambia OLLAMA_MODELS ni solicita sudo. La resolución de descendientes protegidos procede de la captura previa autorizada: no se revalida en vivo ni se leen blobs. Cambios concurrentes del almacén/enlaces son una limitación explícita.

El controlador reserva y sincroniza ledger antes de enviar bytes, escribe resultados exclusivos y checkpoints por hash, y verifica orden/propiedad/presupuesto. Una intención huérfana no se reintenta; STOP crítico no se limpia. `--resume` exige autorización adicional ligada al hash del ledger, comprobación de procesos y conciliación. SIGTERM/SIGKILL pueden dejar evidencia sin STOP final; el ledger y el marcador siguen siendo indispensables. Una futura ejecución persistente no se lanzará hasta aprobación y verificación de ausencia de otro controlador.

Los 32 plazos suman hasta 9600 s de generación más A, metadatos y almacenamiento; no es una cota total de duración. No se ha demostrado consumo máximo de RAM ni tamaño total de artefactos mediante inferencias. Deben conservarse disco y monitorización; no se borra histórico para ganar capacidad.

## Puerta de aprobación pendiente

La revisión humana de las 16 referencias fue confirmada como pendiente por el responsable. Se entregan fichas, estados, criterios y plantillas, con 0 aprobaciones. Primero deben resolverse el bloqueo metodológico de contexto y la revisión; luego vincular el candidato completo, hashes, evidencia, orden, referencias y autorizaciones.

Las cinco autorizaciones siguen pendientes: protocolo definitivo, referencias humanas aceptadas, FREEZE final, presupuesto máximo de 32 inferencias y ejecución F4 en AWS. Este documento no solicita omitir los bloqueos ni concede autorización. No debe sellarse ni ejecutarse este candidato incompleto. Los resultados H1/H2 continúan sin medir.
