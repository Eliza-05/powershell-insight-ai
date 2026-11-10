# Protocolo de Fase 4: Qwen3-Coder v2 (prospectivo)

**Versión:** 1, 10 nov 2026, America/Bogota. **Rama:** `integration/final-validation`.
**Responsable y aprobadora:** Karol. **Redacción:** Claude (IA), a petición de Karol.
**Estado:** APROBADO por Karol el 2026-11-10 10:17 −05:00 ("2 aprobar", en respuesta a la solicitud de aprobar el PROTOCOLO_FASE4 v1). Este documento entra en el manifiesto del candidato (`refresh_candidate`) y queda congelado con el FREEZE. Cualquier cambio posterior exige un candidato nuevo y una nueva aprobación.

> Sustituye prospectivamente la especificación Qwen14 de `docs/phase4_protocol_proposed.md`, que se conserva sin modificar como antecedente histórico. Hereda `docs/methodology.md` y `docs/behavior_taxonomy.md`. Toma como base la propuesta provisional `evidencias-publicables/evaluacion/PROTOCOLO_QWEN3_PROVISIONAL.PUBLICABLE.md`, pero no la reemplaza retroactivamente.

## 1. Hipótesis

- **H1:** el micro-F1 de etiquetas B01–B07 es mayor en C que en B. La diferencia pareada C−B se calcula sobre los 14 casos con referencia determinada. Alternativa: C > B.
- **H2:** el número de afirmaciones factuales no respaldadas por unidad es menor en C que en B, con agregación por bloque. Alternativa: C < B.

No se exige que C gane. Los resultados negativos o nulos se informan igual.

## 2. Condiciones

| | A | B | C |
|---|---|---|---|
| Qué recibe | 1A + 1B deterministas, sin LLM | Original con el preprocesamiento común v2 | Igual que B, más la recuperación 1A verificada |
| Qué nunca recibe | — | Recuperación, etiquetas 1B, referencias, salidas previas | Etiquetas 1B, salidas B, referencias, hipótesis |

B y C comparten modelo, digest, parámetros, política, esquema, sanitizador, verificador y presupuesto de contexto. Solo difiere la recuperación 1A. `Proposal.context` comprueba que el request contenga exactamente `{original}` en B o `{original, deterministic_recovery}` en C.

## 3. Configuración efectiva

| Elemento | Valor |
|---|---|
| Perfil | `PSI_LLM_PROFILE=qwen3coder-v2` (selección explícita; sin fallback) |
| Modelo / digest | `qwen3-coder:30b` / `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca` |
| Estrategia / sanitizador / verificador | `v2-deterministic-layers-2` / `comment-blanking-v2-diagnostics` / `evidence-check-v2-bounded` |
| Política v2 (texto normalizado) | SHA-256 `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081` |
| Opciones | CPU (`num_gpu=0`), temperatura 0, semilla 42, `num_ctx` 8192, `num_predict` 2048, 10 hilos, batch 256, top_k 20, top_p 0,95, min_p 0, repeat_penalty 1, keep_alive 5m; sin `think` |
| Presupuesto de contexto | `message-bytes-scaled-v3`: ceil(bytes × 0,5) + 512 + 2048 ≤ 8192 (enmienda CTX-01, aprobada el 10 nov) |
| Plazo / reintentos | 300 s absolutos por llamada / 0 |
| Proveedor | Ollama solo en `127.0.0.1:11434`; sin descargas automáticas |

Los valores exactos quedan en `configuration.json` del candidato, extraídos del perfil nativo y sin overrides (`prepare` rechaza `unexpected_settings_override`).

## 4. Entorno de ejecución (cambio respecto de la propuesta provisional)

La propuesta provisional se preparó en AWS EC2 (Ubuntu 26.04). AWS cerró esa cuenta el 10 nov 2026 por una verificación de pago pendiente, y la instancia y su binding ya no están disponibles. **El entorno pasa a Google Cloud Compute Engine:**

- Proyecto `psi-cierre`, instancia `psi-cierre`, e2-standard-8 (8 vCPU, 32 GB), zona us-central1-c.
- Ubuntu 24.04.5 LTS, Python 3.13.18 en un venv propio con las dependencias fijadas.
- Ollama 0.40.16, solo CPU, y el mismo digest del modelo.

Los detalles verificados (versiones, recursos, binding y su evidencia) se registran en `INFORME_TECNICO.md` y en el preflight del candidato. El cambio ocurre **antes** de preparar, revisar o congelar el candidato, así que no altera un experimento congelado. La versión de Ollama (0.40.16 frente a 0.40.14–0.40.15 en el laboratorio) queda declarada como diferencia de entorno.

## 5. Datos, referencias y reserva

- **Datos:** 16 unidades F4 (F4-01…F4-16), con 14 referencias determinadas y 2 indeterminadas (`expected_labels = null`). Hay 8 unidades con recuperación 1A y 8 sin ella. Los textos se generan con `experiments/phase4/dataset.py`, sin editar ningún caso.
- **Validez de la reserva (decisión):** el único contacto previo con F4 fue la preparación interrumpida en `7fc29f8`. Produjo 1 request B, ninguna inferencia y ninguna respuesta del modelo. El factor CTX-01 se fijó solo con datos de desarrollo y selección, sin abrir F4. Por eso F4 se mantiene como reserva válida, con esa exposición declarada. Si al preparar algún caso sigue sin caber, **no se cambia el factor**: la unidad se documenta como impedimento.
- **Independencia de casos:** la auditoría automática de `independence.audit` se ejecuta al preparar. Si encuentra un duplicado exacto o de programa, el candidato se detiene. La independencia semántica la aprueba Karol en su revisión (`semantic_independence_approved`).
- **Revisión de referencias:** la hace Karol personalmente, sobre las 16 unidades del candidato y ligada a su hash, antes del FREEZE. **Declaración:** Karol participó en la selección del modelo y en el laboratorio de desarrollo. No participó en redactar las referencias F4; las redactó otra persona (respuesta de Karol, 2026-11-10 10:17 −05:00). Su revisión es humana y nominativa, **no independiente**: no hay segundo revisor, cegamiento ni acuerdo entre revisores. Esta limitación se acepta para el alcance académico del cierre y se repite en los resultados.

## 6. Orden y presupuesto

- Hay 48 pasos: en cada unidad, primero A y luego B y C. El orden de las unidades usa la semilla 40716 y el contrabalanceo B/C la semilla 61407, con 8 unidades B→C y 8 C→B.
- Máximo **32 intenciones LLM**, sin reintentos. Cada intención se reserva en el ledger antes de enviar cualquier byte.
- Se usa un solo controlador en sesión exclusiva y ejecución persistente (`setsid nohup`), sin API web ni demo en paralelo.
- `--resume` solo es válido después de una conciliación y con una nueva autorización ligada al hash del ledger.

## 7. Política de fallos y denominadores

| Evento | Operación | H1 / H2 |
|---|---|---|
| `evidence_check_incoherent` con respuesta terminal íntegra | Se conservan el crudo y el diagnóstico; no se publica predicción ni se reintenta | `predicted = null`; los positivos determinados cuentan como FN de cobertura, sin crédito de conjunto exacto. H2 revisa el crudo si es adjudicable |
| JSON terminal inválido | Se conservan los bytes; no se pide reparación al modelo | No utilizable en H1; en H2 nunca cuenta como cero favorable |
| Terminal por longitud (`done_reason=length`) o `context_limit` posterior | Se registran el crudo, los tokens y los tiempos | Cuenta como no utilizable, con el faltante declarado |
| Timeout, respuesta no terminal, HTTP crítico o recurso fallido | Se conservan el intento y el circuito; el controlador aplica STOP y no hay más despachos | Campaña parcial: solo descriptivos de lo observado, sin contraste completo de H1/H2 |
| Fallo antes de la reserva | Se registran la causa y la ausencia de despacho | No cuenta como llamada |
| Reserva sin resultado o estado incierto | La intención cuenta como gastada; se concilian ledger, proceso y checkpoint | Faltante explícito; no se inventa una salida |
| Referencia indeterminada (2) | Se ejecuta igual en A/B/C | Fuera de las métricas de etiquetas; dentro de la cobertura y del inventario de 16 |

**Contadores obligatorios:** previstos, ejecutados A/B/C, autorizados, reservados, exitosos, timeouts, fallos de proveedor, rechazos, faltantes y cobertura de la revisión humana. `predicted = null` nunca equivale a `[]`.

## 8. Métricas

- **H1 principal:** micro-F1(C) − micro-F1(B) sobre los 14 determinados, con las predicciones **publicadas por el pipeline** (después del verificador). Una etiqueta cruda descartada nunca se promueve.
- **H1 secundarias:** macro-F1 sobre clases con soporte, métricas por clase, conjuntos exactos y parejas en que ambos modos son utilizables (con el sesgo de selección declarado). La cobertura de A es aparte.
- **H2 principal:** número de afirmaciones `insufficient` o `contradicted` por unidad. Las adjudica Karol a partir del inventario completo y deduplicado de **todos** los campos de cada salida cruda de B y C, incluidas las rechazadas, y quedan ligadas al hash de cada salida.
- **H2 secundarias:** la fracción no respaldada, el soporte permisivo y la literalidad de las citas, esta última separada del soporte semántico.
- **Estadística:** intercambio exacto por bloques, bootstrap pareado (2000 remuestreos, semilla 40716) y ajuste de Holm sobre las dos hipótesis primarias, informado junto al p sin ajustar. No hay aceptación automática.
- **Alcance de las conclusiones:** muestra pequeña e intencional, de autoría común. No se hacen afirmaciones poblacionales ni causales.

Todo se calcula con `experiments/phase4/metrics.py` y `evaluation.py` (`evaluate --personal-reviews`), sin cambiar fórmulas después de ver resultados.

## 9. Puertas y aprobaciones (en orden)

| # | Puerta | Estado |
|---|---|---|
| 1 | Enmienda CTX-01 | **Aprobada** por Karol el 2026-11-10 09:47 −05:00 |
| 2 | Este protocolo (incluido el cambio de entorno y la decisión de reserva) | **Aprobado** por Karol el 2026-11-10 10:17 −05:00 |
| 3 | Preparación del candidato con F4 (sin inferencias) | Pendiente de autorización escrita |
| 4 | Revisión personal de las 16 referencias, con independencia semántica y seguridad | Pendiente (Karol) |
| 5 | FREEZE (`seal`) | Después de la puerta 4 |
| 6 | Autorización de ejecución: máximo 32 intenciones, sesión exclusiva, ligada a FREEZE y revisión | Pendiente (Karol) |
| 7 | Revisión semántica H2 de las salidas | Después de la campaña (Karol) |

Ninguna puerta aprueba a las siguientes. Las aprobaciones se transcriben con fecha, hora y frase textual en `RESULTADOS_H1_H2.md`.
