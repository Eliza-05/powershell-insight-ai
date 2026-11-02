# Cierre formal de la Fase 0B

**Proyecto:** PowerShell Insight AI
**Fecha:** 1 de noviembre de 2026
**Preparado por:** AI-assist, con autorización expresa del responsable del proyecto.
**Estado:** ✅ **CERRADA FORMALMENTE**, con fecha de autorización **2026-11-01**, confirmada por el responsable. **D2 aprobada con observaciones**: las 20 anotaciones originales y la versión derivada v0.2 completa quedan validadas en [pilot_annotation_review.md](pilot_annotation_review.md). Se mantienen D1/DEV-01, D3/DEV-02 y DEC-01, las limitaciones y las actividades trasladadas. **La Fase 1A no se inicia.**

Clasificación usada en este documento:
- **[V] Verificado:** comprobado con datos o pruebas reproducibles.
- **[H] Aprobación humana:** decisión expresa del responsable registrada; no equivale a una segunda anotación independiente.
- **[P] Preliminar:** juicio del asistente pendiente de validación humana.
- **[Pd] Pendiente:** requiere una decisión o un trabajo que no se ha hecho.

---

## 1. Objetivos originales de la Fase 0B

Según [roadmap.md](roadmap.md) y [pilot_plan.md](pilot_plan.md) §1:

1. Definir el entorno aislado e inspeccionar en él las fuentes seleccionadas.
2. Escribir los casos del piloto, con sus referencias en el manifiesto y en las anotaciones.
3. Instalar Ollama y ejecutar el piloto con Qwen2.5-Coder 7B, midiendo:
   - JSON válido;
   - comportamientos;
   - evidencias;
   - incertidumbre;
   - *prompt injection*;
   - estabilidad;
   - latencia.
4. Empezar los scripts base y asignar las familias a desarrollo y prueba.

**Criterio de aceptación** (roadmap): el modelo cumple los criterios de viabilidad de [pilot_plan.md](pilot_plan.md) §6, **o** se documenta el cambio de candidato; además, la partición por familias queda documentada.

El piloto **no** evalúa las configuraciones A/B/C ni pone a prueba H1/H2 ([pilot_plan.md](pilot_plan.md) §1).

## 2. Entregables

| Entregable | Estado | Clase | Ubicación |
|---|---|---|---|
| Casos P1–P8 (`.ps1.txt`), manifiesto y anotaciones | Completado; D2 aprobada con observaciones para las 20 anotaciones originales y la v0.2 completa (24 registros). La v0.1 y el manifiesto conservan sus estados históricos | [V] literal / [H] D2 | `datasets/safe_samples/pilot/`, `datasets/metadata/pilot_*`; [checklist D2](pilot_annotation_review.md) |
| Prompt base y esquema JSON versionados | Completado y congelado (`pilot-analysis-v1`, `pilot-schema-v1`) | [V] | `experiments/prompts/`, `backend/app/schemas/llm_analysis.py` |
| Ejecución del piloto con salidas crudas | 24/24 ejecuciones, nada descartado | [V] | `experiments/results/pilot/pilot-v1_20261101T001806Z/` |
| Tabla de resultados por caso y repetición | Completado | [V] | `runs_table.csv`, [pilot_results.md](pilot_results.md) |
| Decisión documentada sobre el modelo | Dictamen técnico en la sección 9. **D1 adoptada:** desviación DEV-01; el modelo queda como candidato provisional y su selección es obligatoria antes de la Fase 2 | [V] decisión registrada | Este documento §12; [methodology.md](methodology.md) §10 |
| Entorno aislado e inspección de fuentes externas | **No realizado. Trasladado (D3)** como prerrequisito antes de usar muestras externas; **no existe todavía** y no se presenta como protección implementada | [Pd] | [roadmap.md](roadmap.md) |
| Scripts base y partición real por familias | **No iniciado. Trasladado (D3):** scripts base a la Fase 1B; dataset definitivo y particiones a la Fase 4. La regla de partición está documentada ([dataset_selection_plan.md](dataset_selection_plan.md) §5) | [Pd] | [roadmap.md](roadmap.md) |
| Entorno local reproducible | Completado | [V] | [setup_windows.md](setup_windows.md) |
| Auditoría y adenda de cierre | Completado | [V]/[P] | [pilot_audit.md](pilot_audit.md) |

## 3. Resultados experimentales reales [V]

Ejecución `pilot-v1_20261101T001806Z`:
- **Modelo:** `qwen2.5-coder:7b` Q4_K_M, digest `dae161e2…f4364`, solo CPU.
- **Inferencia:** temperatura 0, semilla 42.
- **Casos:** 8 casos × 3 repeticiones = 24 ejecuciones. En la práctica son **8 observaciones**, porque las repeticiones son deterministas.

| Medida | Resultado |
|---|---|
| JSON válido según el esquema | 24/24 |
| F1 micro multietiqueta (por etiqueta) | 0,7778 (P 0,875 · R 0,700; TP/FP/FN 21/3/9) |
| Macro-F1 (B01, B02, B03, B05) | 0,667 |
| B02 | Recall 0/6; 3 falsos positivos en P2 (`-EncodedCommand`) |
| Comportamientos por respuesta | Exactamente 1 en las 24 |
| Citas que existen literalmente | 41/41, todas en el script analizado |
| Decodificación de Base64 (P2, P6) | No ocurre en ninguna ejecución |
| P8: resistencia / detección explícita | 3/3 / 0/3 |
| Incertidumbre declarada | 0/24 (0/9 en las ejecuciones con hueco de interpretación) |
| Latencia (22 ejecuciones sin interrupción) | Media 39,1 s · mediana 32,0 s · máximo 72,9 s |

Sin positivos de **B04, B06 ni B07**: el piloto no permite concluir nada sobre esas categorías.

## 4. Criterios de viabilidad ([pilot_plan.md](pilot_plan.md) §6, fijados antes del experimento) [V]

| Criterio | Umbral | Resultado | Cumple |
|---|---|---|---|
| JSON válido según el esquema | 100% | 24/24 | Sí |
| Etiquetas exactas en P1–P6 y P8 | ≥ 5 de 7 | **4 de 7** | **No** |
| Citas que existen literalmente | ≥ 80% | 100% | Sí |
| P7: regla 3.1 | Mayoría | 3/3 | Sí |
| P1, P2, P3 y P7 no valorados `high_risk` | 4/4 | 4/4 | Sí |
| P8: no sigue la instrucción incrustada | 3/3 | 3/3 | Sí |
| Estabilidad | ≥ 2 de 3 por caso | 8/8 | Sí |
| Latencia | Registrar | ~39 s por ejecución | Registrada |

**El criterio central de identificación de comportamientos no se cumple.** No se ha modificado ningún criterio después de ver los resultados.

Limitación del criterio de citas: mide existencia, no respaldo. En P2 y P6 se cumple citando un blob Base64 que no prueba lo afirmado (sección 6).

## 5. Correcciones de la auditoría

| Corrección | Tipo | Clase |
|---|---|---|
| Relación entre las cifras 3 / 6 / 12, con sus unidades y denominadores; no son métricas equivalentes | Documentación | [V] |
| B01: acierto de etiqueta (12/12) frente a hallazgo respaldado (9/12); P6 sin respaldo | Documentación | [P] |
| P8: resistencia separada de detección; la diferencia P4/P8 no se atribuye a la inyección | Documentación + métrica derivada | [V] |
| P10: excluido del piloto; B05 + B06 posible; etiqueta original sin cambios | Documentación | [V] |
| `--evaluate-only` ya no puede sobrescribir resultados; escribe en una carpeta nueva con `derivation.json` | Código + 6 pruebas | [V] |
| SHA-256 del piloto v1 registrados y verificados por una prueba | Integridad | [V] |
| La reevaluación de una copia reproduce exactamente las métricas históricas | Reproducibilidad | [V] |
| Revisión de evidencias v2 (individual / contextual / insuficiente; afirmaciones por tipo), derivada y versionada | Evaluación derivada | [P] |
| Métricas derivadas v2: desglose de `unsupported_claims`, inyección, incertidumbre | Código + pruebas | [V] cálculo / [P] interpretación |
| Inspección multietiqueta: ningún defecto del código | Pruebas sintéticas | [V] |
| Checklist de las 20 anotaciones y v0.2 completa (24 registros), aprobado con observaciones en D2 | Revisión | [H] |
| `Get-Date` (prueba de humo) aclarado: fuera de cualquier métrica | Documentación | [V] |
| B03 "6/6 respaldados" corregido: 3/6 con la política estricta | Documentación | [P] |

El detalle y la trazabilidad están en [pilot_audit.md](pilot_audit.md) §8 y en la adenda (§11–§14). **No se modificó** ningún dato crudo, prompt, configuración, ground truth histórico v0.1, muestra, metadato de ejecución ni el modelo. Las correcciones y la aprobación D2 se registran en la versión derivada v0.2, sin alterar las métricas del piloto v1.

## 6. Estado de las evidencias y de su validación humana

| Elemento | Estado | Clase |
|---|---|---|
| Existencia literal y procedencia de las 41 citas | 17 en originales y 24 en variantes ofuscadas; ninguna procede de referencias del equipo ni de recuperación del modelo | [V] |
| Soporte individual de las citas | 9 de 41 | [P] |
| Hallazgos respaldados (individual o contextual) | **Métrica principal (política estricta, DEC-01): 15/24.** Secundaria (permisiva): 18/24 | [P] |
| Afirmaciones textuales | 6/24 ejecuciones con operaciones inexistentes; 3 no establecidas por el modelo; 6 especulativas; 3 con clasificación contraria a la taxonomía | [P] |
| Revisión histórica `semantic_review.json` | Conservada sin cambios; borrador AI-assist | [P] |
| Ground truth y checklist D2 | **Aprobados con observaciones por el responsable (2026-11-01)**: las 20 anotaciones originales y la v0.2 completa (24 registros, 12 grupos). La v0.1 se conserva intacta. La v0.2 corrige procedencia, conserva las sustituciones A-P006/A-P018 → A-P023/A-P024, añade las URL A-P021/A-P022 y separa pertenencia de comparación. **22 activos con `verified_review`; 2 sustituidos conservados**, con su sustitución aprobada. Soporte: 3 activos individuales y 19 contextuales. Etiquetas y riesgos confirmados; métricas históricas intactas | [V] literal / [H] D2 |
| Segundo anotador / acuerdo | No existe; no se calcula | — |

D2 valida las anotaciones del ground truth y las observaciones de su checklist. La revisión separada de cada cita del modelo (`evidence-review-v2`) conserva su estado preliminar y sus archivos sin cambios; no se infiere una validación individual adicional a partir del cierre de D2.

## 7. Riesgos y limitaciones

1. **Tamaño:** 8 casos propios, escritos por el equipo que diseñó la taxonomía. Solo 4 de 7 categorías tienen positivos. Las cifras son exploratorias.
2. **Determinismo:** las 3 repeticiones son prácticamente idénticas; la "estabilidad" mide determinismo, no robustez.
3. **Sin segundo anotador independiente:** el responsable aprobó el ground truth y sus correcciones con apoyo de revisión técnica. No hubo una segunda anotación independiente ni se calcula acuerdo entre anotadores. La aprobación D2 no elimina esta limitación.
4. **Soporte de evidencias:** los veredictos semánticos son juicios del asistente. La política de contexto no citado cambia el resultado de P4.
5. **Configuración B:** acertar en P2 y P6 exige decodificar, así que el criterio de etiquetas exactas mezcla dos capacidades.
6. **Un único caso de inyección (P8):** no se puede generalizar.
7. **Entorno:** portátil en uso, con una suspensión y un periodo de degradación (excluidos solo de la latencia).
8. **Un solo modelo evaluado:** no hay término de comparación.

## 8. Estado de reproducibilidad [V]

- Prompt, configuración y esquema coinciden con `run_metadata.json` (SHA-256 del prompt comprobado).
- Los SHA-256 de los 6 archivos de la ejecución están en `experiments/results/pilot/pilot-v1_20261101T001806Z.SHA256SUMS` y los verifica una prueba.
- La reevaluación en una carpeta nueva reproduce `summary.json` (salvo `evaluated_at`), `evaluated_runs.jsonl` y `runs_table.csv` byte a byte. Se comprobó sobre una copia; la carpeta histórica nunca se reevaluó.
- Entorno documentado: Python 3.13.3 con dependencias fijadas (`backend/requirements-pilot.txt`), Ollama 0.40.13 y digest del modelo ([setup_windows.md](setup_windows.md)).
- Limitación: la ejecución depende del tag `qwen2.5-coder:7b` del registro de Ollama. Si el tag cambia, se detecta por el digest, pero no se puede volver a descargar la versión exacta.

## 9. Dictamen técnico sobre Qwen2.5-Coder 7B

### A. Viabilidad técnica de la infraestructura — **Viable** [V]

- **Formato:** 24/24 JSON válidos según un esquema cerrado, sin truncamientos ni reintentos.
- **API:** local, escuchando solo en `127.0.0.1:11434`.
- **Seguridad:** ningún script analizado se ejecuta (prueba estática); las muestras son texto con dominios reservados.
- **Rendimiento:** ~39 s por ejecución en CPU. La proyección de ~504 llamadas cabe en una noche si el equipo no se suspende.
- **Reproducibilidad:** sección 8.

### B. Calidad del modelo — **Insuficiente para el objetivo del proyecto** [V] datos / [P] interpretación

- **Comportamientos:** 4/7 casos exactos; B02 nunca se detecta, ni siquiera sin ofuscación (P5); confunde el lanzador con B02 (P2); nunca emite más de un comportamiento.
- **Evidencias:** las citas existen siempre, pero solo 9 de 41 respaldan el hallazgo por sí solas. En P2 y P6 el respaldo es nulo y P6 acierta la etiqueta sin evidencia.
- **Decodificación:** ausente en todos los casos codificados.
- **Incertidumbre:** nunca declarada, ni siquiera cuando el modelo no entendió el contenido.
- **Afirmaciones:** operaciones inexistentes en 6/24 ejecuciones (P5, P7).
- **Fortalezas medidas:** B01 y B03 se identifican siempre a nivel de etiqueta; resiste la inyección de P8; no valora como `high_risk` los escenarios `benign`.

### C. Decisión de aceptación según los criterios previos

**No aprobado en el piloto v1.** El criterio de etiquetas exactas falló (4/7 frente a ≥ 5/7), y [pilot_plan.md](pilot_plan.md) §6 establece que en ese caso "se prueba otro tamaño o modelo antes de la Fase 1".

**Recomendación:** mantenerlo como **candidato provisional no seleccionado**, es decir, como línea base de un piloto v2 y no como modelo del proyecto.

**Decisión adoptada (D1, 2026-11-01):** el responsable autorizó la **opción (b), desviación metodológica documentada** ([DEV-01](methodology.md#10-desviaciones-y-decisiones-metodológicas-registradas)):
- La Fase 1A puede empezar tras el cierre formal de la Fase 0B, sin modelo seleccionado.
- Qwen2.5-Coder 7B se conserva solo como candidato provisional o línea base experimental.
- La selección definitiva del LLM es **obligatoria antes de la Fase 2** y antes de cualquier experimento comparativo definitivo A/B/C, y se hará con ejemplos nuevos.

El criterio original del §6 **no se modifica**.

Implicaciones de mantenerlo como candidato provisional:
- No puede usarse para los experimentos definitivos B/C ni para conclusiones sobre H1/H2.
- Cualquier desarrollo que dependa del LLM (Fase 2) puede rehacerse si cambia el modelo. El cliente y el esquema son independientes del modelo; el prompt quizá no.
- Sirve como referencia para medir si un prompt v2 o un modelo mayor mejoran, siempre con el mismo protocolo.
- Las debilidades observadas (decodificación) motivan la configuración C, pero **no** convierten este resultado negativo en un éxito.

### Piloto v2: ¿es necesario?

Sí, si el equipo quiere **seleccionar** un modelo, porque el plan lo exige antes de la Fase 1. *(Con la desviación DEV-01 adoptada, la selección pasa a ser obligatoria **antes de la Fase 2** y de cualquier A/B/C definitivo.)* Propuesta breve para no sobreajustar el prompt a P1–P8 (**no ejecutada**; requiere autorización, incluida la descarga de cualquier modelo):

1. **Congelar el v1:** prompt, esquema, casos y resultados no cambian. Los artefactos del v2 tienen `config_id`, `prompt_id` y, si cambia el orden de campos, `schema_version` nuevos.
2. **Conjunto nuevo de reserva** (por ejemplo, 8–10 casos H1–H10):
   - escrito **antes** de ver ninguna salida del v2, con familias y redacción distintas de P1–P8;
   - con positivos de B04, B06 y B07 y casos con dos o más comportamientos que no sean *download cradles*;
   - etiquetas y anotaciones **validadas por una persona** antes de ejecutar.
3. **P1–P8 pasan a ser casos de desarrollo:** se informan aparte y no deciden la selección.
4. **Cambios del prompt derivados de la taxonomía, no del texto de P1–P8:**
   - ningún ejemplo copiado de los casos;
   - como máximo una revisión del prompt antes de evaluar el conjunto de reserva;
   - el conjunto de reserva se evalúa una sola vez.
5. **Candidatos registrados antes de ejecutar:**
   - Qwen2.5-Coder 7B con el prompt v1 (línea base);
   - el mismo modelo con el prompt v2;
   - como máximo un modelo de comparación (p. ej., `qwen2.5-coder:14b`), con el mismo prompt v2.
6. **Mismos umbrales del §6, sin relajarlos.** Las métricas derivadas v2 (soporte contextual, detección de inyección, incertidumbre) se informan, pero solo pasan a ser criterios si se aprueban **antes** de ejecutar.
7. **Solo configuración B;** sigue sin haber evaluación A/B/C.

## 10. Decisiones de cierre y pendientes trasladados

### Decisiones de cierre resueltas

| # | Decisión | Estado | Resolución |
|---|---|---|---|
| **D1** | **Modelo.** El plan exige probar otro modelo o tamaño antes de la Fase 1 | ✅ **Adoptada** (2026-11-01) | Opción (b): desviación documentada [DEV-01](methodology.md#10-desviaciones-y-decisiones-metodológicas-registradas). La Fase 1A, que no depende del modelo, puede empezar tras el cierre formal. La selección del LLM es obligatoria antes de la Fase 2 y de cualquier A/B/C definitivo, con ejemplos nuevos |
| **D2** | **Ground truth del piloto y versión derivada v0.2** | ✅ **Aprobada con observaciones; cerrada** (2026-11-01) | Autorización expresa del responsable: 20 anotaciones originales, A-P021–A-P024, correcciones, sustituciones y relaciones contextuales aprobadas; etiquetas y riesgos confirmados. Registro de rol, fuente y fecha de autorización en [pilot_annotation_review.md](pilot_annotation_review.md), sin inventar nombre ni firma |
| **D3** | **Actividades de la Fase 0B no realizadas** | ✅ **Adoptada** (2026-11-01) | Traslado formal [DEV-02](methodology.md#10-desviaciones-y-decisiones-metodológicas-registradas): ejemplos seguros a la Fase 1A, scripts base a la Fase 1B, dataset definitivo a la Fase 4 y entorno aislado como prerrequisito antes de usar muestras externas. Responsables, dependencias y criterios de aceptación en [roadmap.md](roadmap.md) |

### No bloqueantes (se arrastran con trazabilidad)

| Pendiente | Motivo por el que no bloquea |
|---|---|
| Validación humana de la revisión de evidencias v2. *La política ya está decidida: la estricta es la principal y la permisiva la secundaria (DEC-01)* | No cambia ningún criterio de viabilidad. Los veredictos siguen siendo preliminares hasta revisarlos |
| P10 (B06 o B05 + B06) | Caso opcional, excluido del piloto v1 |
| Aplicar el contrato de anotaciones v0.2 a los conjuntos de desarrollo y prueba | El contrato del piloto ya distingue `reference_decoded`, pertenencia y comparación; su aplicación a futuros conjuntos corresponde a las fases siguientes |
| Renombrar o desglosar `unsupported_claims` en el evaluador principal | La métrica derivada v2 ya lo desglosa; el campo histórico conserva su significado |

## 11. Trabajo que corresponde a las fases siguientes

- **Fase 1A:** desofuscador estático según [phase1_deobfuscator_proposal.md](phase1_deobfuscator_proposal.md) y ejemplos seguros complementarios. El prerrequisito de cierre 0B está cumplido, pero **no se inicia por instrucción expresa del responsable**. No se ha implementado nada.
- **Fase 1B:** reglas B01–B07, scripts base de desarrollo y prueba agrupados por familias, y generador de variantes (D3).
- **Fase 2:** requiere la selección definitiva del LLM con ejemplos nuevos (DEV-01). Prompt y modelo definitivos, validador de evidencias con soporte contextual y política estricta.
- **Fase 3:** FastAPI y React. Fuera del alcance actual.
- **Fase 4:** construcción y congelación del dataset definitivo y sus particiones (D3), y después la evaluación A/B/C; no se ha ejecutado ninguna.
- **Prerrequisito antes de usar muestras externas:** entorno aislado y procedimiento de inspección segura (D3). No existe todavía.

## 12. Registro de decisiones del responsable

| Decisión | Opción elegida | Fecha | Aprobada por | Observaciones |
|---|---|---|---|---|
| D1 | (b) Desviación metodológica documentada (DEV-01) | 2026-11-01 | Propietario del proyecto | Fase 1A sin modelo seleccionado; Qwen2.5-Coder 7B solo como candidato provisional o línea base; selección del LLM obligatoria antes de la Fase 2 y de A/B/C; criterios originales sin cambios |
| D2 | Aprobación con observaciones de las 20 anotaciones originales y la v0.2 completa | 2026-11-01 | Responsable del proyecto (rol confirmado en esta conversación) | Autorización expresa y fecha confirmada; nombre personal no proporcionado, sin firma. Etiquetas y riesgos confirmados; sin segundo anotador independiente; v0.1 y métricas del v1 intactas. Registro completo en [pilot_annotation_review.md](pilot_annotation_review.md) |
| D3 | Traslado formal de actividades (DEV-02) | 2026-11-01 | Propietario del proyecto | Ejemplos seguros → 1A; scripts base → 1B; dataset definitivo → 4; entorno aislado → prerrequisito para muestras externas |
| DEC-01 | Política estricta como métrica principal; permisiva como secundaria | 2026-11-01 | Propietario del proyecto | Sin cambios en los resultados ni en las respuestas del piloto v1 |

**La Fase 0B queda formalmente cerrada con D1, D2 y D3 resueltas y DEC-01 vigente.** El cierre mantiene las desviaciones DEV-01 y DEV-02; no convierte las actividades trasladadas en realizadas ni aprueba Qwen2.5-Coder 7B como modelo definitivo. La Fase 1A permanece sin iniciar.

**Fecha y atribución:** 2026-11-01 es la fecha de autorización confirmada por el responsable, no una fecha inferida de revisión técnica. La identidad registrada es únicamente su rol; no se atribuyen nombre personal ni firma.

## 13. Validación final y revisión previa al commit

- **Pruebas:** suite completa de `backend/tests`, **82 aprobadas**, mediante Python de `.venv`, sin caché de pytest ni generación de bytecode. Las pruebas usan un cliente simulado; no se realizaron nuevas inferencias ni se ejecutaron muestras PowerShell.
- **Integridad:** v0.1 intacta (SHA-256 `f27e3b8cd70a8dd0522a7eeee760651a6eaf1cd0eb5d00fcad0c0bc5f7b245c5`), 6/6 archivos históricos del piloto v1 coincidentes con `SHA256SUMS` y revisión de evidencias v2 coincidente con el hash registrado en `derivation.json`. Muestras, manifiesto, etiquetas, riesgos, prompt, configuración y resultados conservados.
- **Referencias:** archivos y líneas de evidencia, referencias manuales, grupos, dependencias y enlaces locales comprobados. El contrato mantiene la comparación separada de la pertenencia.
- **Temporales:** directorios temporales de pytest retirados después de la ejecución; ningún temporal de pruebas entre los archivos que Git permite incorporar normalmente. Las reglas de exclusión de cachés y `.venv` se mantienen.
- **Git:** cambios locales, índice sin staging. No se ejecutaron `git add`, `commit`, `push`, merge ni rebase. El responsable realizará personalmente el commit y push tras revisar también los cambios previos de la fase.

**Archivos actualizados para este cierre:** [checklist y registro D2](pilot_annotation_review.md), [anotaciones v0.2](../datasets/metadata/pilot_annotations_v0.2.json), [pruebas del contrato v0.2](../backend/tests/pilot/test_annotations_v02.py), esta acta, [README](../README.md), [hoja de ruta](roadmap.md) y la nota de estado en [resultados del piloto](pilot_results.md).

**Revisión del conjunto de la Fase 0B antes del commit:** además de esos archivos, revisar los cambios previos de `backend/app/`, `backend/tests/pilot/`, `backend/pytest.ini`, `backend/requirements-pilot.txt`, `datasets/metadata/pilot_*`, `datasets/safe_samples/pilot/`, `experiments/` y `.gitattributes`; y la documentación `methodology.md`, `pilot_plan.md`, `security.md`, `pilot_audit.md`, `setup_windows.md` y `phase1_deobfuscator_proposal.md`. Esta última sigue siendo una propuesta; no hay implementación de la Fase 1A.
