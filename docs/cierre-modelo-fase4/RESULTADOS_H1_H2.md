# Resultados de Fase 4 — H1 y H2

**Responsable:** Karol. **Cálculo y redacción:** Claude (IA), con el código congelado y sin cambiar fórmulas después de ver resultados.
**Estado:** campaña **completa**; **H1 y H2 evaluadas** con el código congelado. Resultado: **ninguna de las dos hipótesis tiene apoyo** (§5 y §6).

> Todo lo que sigue procede de datos reales de la campaña 3. Este documento no reproduce scripts, referencias ni salidas F4; su ubicación restringida y sus hashes están en `EVIDENCIAS.md`. Las revisiones humanas son de Karol, son nominativas y **no son independientes** (ver §7).

## 1. Identidad del experimento

| Elemento | Valor |
|---|---|
| SHA científico (código desplegado) | `41330339abc5ba8a73ca6b595c9ed4396d275e82` |
| Protocolo | `PROTOCOLO_FASE4.md` v1, aprobado por Karol el 2026-11-10 10:17 −05:00 |
| Candidato / FREEZE | `d960f81b8a5adb352ade6df80a767b882121c19a3b34eb7cec7ed3ca22255225` / `f0468a2d22575fa7dbc1f5de352602852ed1f73e459d3eea1bbb50ac0be16589` |
| Revisión de referencias (ratificación) | `e0f6190d…`: Karol Estupiñan, 2026-11-10 13:15 −05:00, 16/16 aprobadas, independencia semántica y seguridad aprobadas |
| Autorización de ejecución | `7ccbb881…`: máximo 32, sin reintentos, sesión exclusiva; frase textual de Karol, 2026-11-10 13:16 −05:00 |
| Entorno | GCP n2-custom-12-49152, Ubuntu 24.04.5, Ollama 0.40.16, `qwen3-coder:30b` (digest `06c1097e…`) |
| Ejecución | 2026-11-10, de 18:19 a 18:44 UTC (`COMPLETED.json`: 16 A + 32 intenciones, `operationally_complete: true`) |
| Evaluación oficial | `experiments.phase4 evaluate --personal-reviews`, archivo `13662845…json` (sha256 `15ff07f7…`). La evaluación previa sin revisiones (`c9660947…`, sha256 `f7b20b42…`) se conserva. Resumen agregado: `evidencias-publicables/evaluacion/EVALUACION_F4_CAMPANA3_AGREGADA.json` |

## 2. Aprobaciones transcritas

| Puerta | Frase textual y hora (America/Bogota) |
|---|---|
| Enmienda CTX-01 | "apruebo la enmienda", 2026-11-10 09:47 |
| Protocolo v1 y autoría | "1. otra persona 2 aprobar", 10:17 |
| Preparación del candidato | "autorizo preparar el candidato", 10:37 |
| `vm.overcommit_memory = 0` y re-preparación | "Autorizo cambiar vm.overcommit_memory a 0 en la VM y preparar de nuevo el candidato en una copia nueva.", 12:07 |
| Máquina más rápida y prueba de velocidad (desarrollo) | "Elijo B: autorizo crear una VM c3-standard-22 y hacer una prueba de velocidad con ~6 llamadas de desarrollo (no F4)", 12:39 (la cuota de la cuenta solo permitía n2-custom-12) |
| Candidato nuevo y calentamiento (desarrollo) | "Autorizo preparar un nuevo candidato en copia nueva y hacer 1 llamada de calentamiento con un caso de desarrollo antes de la campaña", 13:07 |
| FREEZE y ejecución (campaña 3) | "Apruebo sellar el FREEZE del candidato d960f81b. Autorizo la ejecución de Fase 4 con un máximo de 32 llamadas, sin reintentos y en sesión exclusiva.", 13:16 |
| Revisión H2 personal | Archivo guardado a las 13:55 (página disponible desde las 13:46). A la pregunta explícita sobre la autoría, Karol respondió: "La hice yo personalmente, leyendo cada salida", 14:06 |

## 3. Intentos anteriores (incidentes conservados)

Ningún intento anterior produjo una respuesta del modelo sobre F4. Por eso no hubo exposición de salidas antes de la campaña 3.

| Campaña | Candidato / FREEZE | Qué pasó | Consumo |
|---|---|---|---|
| 1 | `cfc1cc98` / `cf560115` | El preflight rechazó `vm.overcommit_memory = 1` de la imagen de GCP | 1 A, **0** intenciones LLM |
| 2 | `637dcd0b` / `d13b8173` | Timeout de 300 s en la primera llamada (F4-11 B) en e2-standard-8, sin respuesta | 1 A, **1** intención (gastada, sin reintento) |
| 3 | `d960f81b` / `f0468a2d` | Completa | 16 A, **32** intenciones |

Las campañas 1 y 2 conservan su STOP, ledger, resultados y checkpoints sin modificar. Sus hashes están en `run-r2_final_hashes.txt` y en los respaldos indexados en `EVIDENCIAS.md`. Las tres usan los mismos 16 casos, las mismas 32 solicitudes y el mismo orden, idénticos byte a byte.

## 4. Contadores (protocolo §7)

| Contador | Valor |
|---|---|
| Unidades previstas / determinadas / indeterminadas | 16 / 14 / 2 |
| A ejecutados | 16 (2 con cobertura completa, 14 parciales) |
| Intenciones LLM autorizadas / reservadas / con respuesta terminal | 32 / 32 / 32 |
| Timeouts / fallos de proveedor / paradas | 0 / 0 / 0 |
| B: completadas / no utilizables | 16 / 0 |
| C: completadas o parciales / no utilizables (`invalid_response`) | 12 / 4 |
| Latencia LLM (total_duration): mediana / máximo | 41,2 s / 95,3 s |

## 5. H1: micro-F1(C) − micro-F1(B) sobre los 14 determinados

| Modo | TP | FP | FN | Micro-F1 | Conjuntos exactos | No utilizables |
|---|---|---|---|---|---|---|
| A (1A + 1B) | 0 | 0 | 17 | 0,00 | 3/14 | 0 |
| B | 0 | 0 | 17 | 0,00 | 3/14 | 0 |
| C | 0 | 0 | 17 | 0,00 | 3/14 | 4 |

- **Δ micro-F1 (C − B) = 0,00.** Intercambio exacto por bloques (13 bloques, 8192 asignaciones): p unilateral = 1,0. Bootstrap pareado (2000, semilla 40716): IC 95 % [0,00, 0,00]. Holm (H1, H2): p ajustado = 1,0.
- **Lectura:** los datos **no apoyan H1**. Tampoco la contradicen en sentido opuesto: en ambos modos el pipeline no publicó ninguna etiqueta.
- **Mecanismo, observado en los agregados operativos:**
  - El modelo propuso 13 comportamientos en B y 6 en C. El verificador de evidencia conservador (`evidence-check-v2-bounded`) **descartó los 19**, así que las 32 salidas publicaron conjuntos vacíos.
  - Los 3 conjuntos exactos corresponden a las unidades determinadas cuya referencia es vacía.
  - El protocolo (§8) prohíbe promover etiquetas crudas descartadas a H1. Por eso no se recalcula nada con ellas.
- **Secundarias:**
  - Parejas en que ambos modos son utilizables: 12, con el mismo resultado (0 TP).
  - Citas literales correctas sobre las respuestas parseables: B 16/16; C 12/16 (4 atribuidas a la recuperación).
  - La métrica de citas no mide soporte semántico.
- **Interpretación prudente:**
  - El resultado describe el **pipeline completo** (modelo + capas deterministas), no la capacidad aislada del LLM.
  - El verificador revisado se integró en `develop` después de la exploración del laboratorio y no tenía una evaluación independiente previa (lo advierte `strategy.py`). En estos casos nuevos se comportó como un filtro que lo anula todo.
  - Muestra pequeña e intencional, de autoría común: sin conclusiones poblacionales ni causales.

## 6. H2: afirmaciones no respaldadas por unidad (C − B)

**Revisión:** la hizo Karol personalmente sobre las 32 salidas crudas, incluidas las 4 rechazadas de C. Partió de un inventario segmentado mecánicamente y lo editó ella. El validador oficial aceptó las 32 revisiones (hash de cada salida, citas literales, inventario completo).
Archivo: `revision_H2_Karol.json`, sha256 `9ad26920…`. Archivos por salida: `SPLIT_MANIFEST.json`, sha256 `2a6dcb0c…`.

| Modo | Afirmaciones | `individual` | `contextual_cited` | `insufficient` | `contradicted` | No respaldadas (estricto) | Fracción (secundaria) |
|---|---|---|---|---|---|---|---|
| B | 75 | 9 | 47 | 10 | 9 | **19** | 25,3 % |
| C | 125 | 8 | 99 | 14 | 4 | **18** | 14,4 % |

- **Primaria:** media por bloque de (no respaldadas C − no respaldadas B) = **−0,033** afirmaciones por unidad. Intercambio exacto de signos por bloques (32 768 asignaciones): p unilateral (C < B) = **0,50**. Holm: p ajustado = 1,0.
- **Diferencias por unidad:** 6 unidades con C mejor, 4 con C peor y 6 iguales. Los valores van de −2 a +2.
- **Reconstrucciones inventadas o alteradas:** 0 en B y 0 en C.
- **Lectura:**
  - Los datos **no apoyan H2**: C no reduce de forma apreciable el número de afirmaciones no respaldadas por unidad.
  - C hace más afirmaciones (125 frente a 75), de modo que su fracción no respaldada es menor (14 % frente a 25 %). Esa medida es secundaria, no se planteó como prueba principal y no debe leerse como confirmación.
  - Ninguna de las 32 salidas publicó etiquetas (§5). H2 evalúa el texto crudo completo del modelo, no las etiquetas publicadas.

## 7. Limitaciones

- **Revisora única, no independiente.** Karol hizo la revisión de referencias y la de H2. La de H2 se completó en una sola sesión corta (≈9 min registrados para 200 afirmaciones); Karol confirmó por escrito que la hizo personalmente. Participó en la selección del modelo y en el laboratorio. No redactó las referencias F4. No hay segundo revisor, cegamiento ni acuerdo entre revisores.
- **Entorno distinto del laboratorio.** CPU distinta y Ollama 0.40.16. Hubo una llamada de calentamiento con un caso de desarrollo para que la primera carga en frío cupiera en el plazo, que no cambió (protocolo intacto).
- **Contaminación de F4.** Las campañas 1 y 2 tocaron F4 sin producir salidas, como consta en §3.
- **Muestra.** Son 16 unidades en 13 bloques; la potencia estadística es mínima.
