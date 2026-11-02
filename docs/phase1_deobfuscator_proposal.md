# Propuesta: inicio de la Fase 1 — desofuscador estático

**Proyecto:** PowerShell Insight AI
**Estado:** **propuesta**, pendiente de aprobación del equipo. No se ha implementado nada.
**Fecha:** 1 de noviembre de 2026
**Origen:** [pilot_audit.md](pilot_audit.md) y [pilot_results.md](pilot_results.md) §H.

## 1. Por qué empezar por aquí

- El piloto mostró que el modelo **no decodifica Base64** (P2, P6). Sin decodificar, inventa o cambia comportamientos y declara una incertidumbre baja. Recuperar el contenido de forma estática es la base de la configuración C y de la pregunta de investigación.
- El desofuscador es la parte de la configuración A que **no depende del modelo**. La decisión pendiente sobre el modelo o el prompt v2 no lo bloquea.
- El repositorio ya tiene contratos, utilidades y casos de prueba que se pueden reutilizar.

## 2. Alcance de este primer incremento

**Incluye:**

- El servicio `backend/app/services/deobfuscation/`, en Python puro, sin FastAPI.
- Las cuatro técnicas con cobertura `supported` en [dataset_selection_plan.md](dataset_selection_plan.md) §4.1: `OT-B64-ENCCMD`, `OT-B64-INLINE`, `OT-CONCAT` y `OT-VARSUB`.
- La **detección sin resolución** de `OT-FORMAT`, que se reporta como fragmento no resuelto.
- La composición de capas (P6: concatenación dentro de Base64), con límites de profundidad, tamaño y tiempo.
- Trazabilidad de cada artefacto recuperado: técnica, posición original y capa de origen.
- Pruebas Pytest con muestras inertes.

**No incluye (incrementos posteriores):**

- Las reglas de detección B01–B07 (`services/detection`), incluida la prioridad de B02 identificada en el piloto.
- El generador determinista de variantes.
- Los endpoints FastAPI y la interfaz React.
- Cambios en el cliente LLM, en el prompt v1 o en el esquema `pilot-schema-v1`.
- Ejecuciones de las configuraciones A/B/C, el piloto v2 y la descarga de modelos.
- Las familias de Invoke-Obfuscation (`OT-IO-*`).

## 3. Reutilización de módulos existentes

| Módulo existente | Reutilización |
|---|---|
| `backend/app/schemas/llm_analysis.py` → `ObfuscationTechnique` | Identificadores de técnica de los artefactos. Mismo vocabulario que la salida del LLM, así A y C son comparables. No se modifica el enum |
| `experiments/evaluation/reference_recovery.py` | Su expresión regular de `-EncodedCommand` y la decodificación UTF-16LE con `validate=True` son el punto de partida de `OT-B64-ENCCMD`. **El archivo no se toca:** sigue siendo la referencia congelada del piloto. Una prueba exige que el desofuscador produzca **exactamente** el mismo texto que `decode_encoded_commands` en P2 y P6 |
| `backend/app/services/evidence/literal_check.py` → `locate(snippet, analyzed, references)` | Los artefactos recuperados se pasan como `references`. Así, una cita del LLM sobre contenido decodificado queda como `REFERENCE_EXACT` en la configuración C, sin cambiar el módulo |
| `datasets/metadata/pilot_manifest.csv` → `deobfuscator_coverage`, `expected_recovered_strings` | Oráculo de las pruebas de recuperación: P2 (`Get-Process`), P3 (URL e `Invoke-WebRequest`), P4 (ruta `Run` y `PilotLabUpdater`), P6 (URL, `Net.WebClient` y `DownloadString`) y P7 (`unsupported`) |
| `datasets/safe_samples/pilot/` y `reference/` | **Fixtures de regresión**, leídas como texto. No son datos de evaluación: los casos `split = pilot` siguen sin usarse en desarrollo ni en prueba ([pilot_plan.md](pilot_plan.md) §2) |
| `backend/tests/pilot/test_pilot_dataset.py::test_pilot_code_never_executes_analyzed_content` | Ya recorre `backend/app`, así que cubre el nuevo servicio sin cambios: prohíbe `eval`, `exec`, `subprocess`, `os.system` y la invocación de PowerShell |
| `backend/pytest.ini` | Sin cambios: las nuevas pruebas van en `backend/tests/deobfuscation/` |

## 4. Diseño propuesto

### 4.1 Contratos (`backend/app/schemas/deobfuscation.py`, nuevo)

```text
SourceSpan            layer_id, start, end (offsets), line
RecoveredArtifact     artifact_id, technique: ObfuscationTechnique, source: SourceSpan,
                      text, layer_id (capa nueva que genera, si aplica), depth
UnresolvedFragment    source: SourceSpan, technique_hint: ObfuscationTechnique | None, reason
DeobfuscationResult   input_sha256, layers (texto de cada capa), artifacts, unresolved,
                      techniques_detected, limits_hit
```

Todos los modelos usan `extra="forbid"`, como `AnalysisResult`. El resultado es serializable a JSON para registrarlo en los experimentos.

### 4.2 Componentes (`backend/app/services/deobfuscation/`)

| Archivo | Responsabilidad |
|---|---|
| `lexer.py` | Tokenizador mínimo de PowerShell en Python: comentarios `#` y `<# #>`, cadenas `'…'` y `"…"` (incluidas las comillas duplicadas), variables y operadores `+` y `-f`. Sirve para **no transformar comentarios** (P8) y para reconocer literales. No usa el parser de PowerShell: invocarlo exigiría lanzar un proceso PowerShell, lo que prohíbe [architecture.md](architecture.md) |
| `transforms/encoded_command.py` | `OT-B64-ENCCMD`: argumento de `-EncodedCommand` en un lanzador `powershell`/`pwsh`. Decodifica el Base64 como UTF-16LE con validación estricta; si falla, genera un `UnresolvedFragment` en lugar de una excepción |
| `transforms/inline_base64.py` | `OT-B64-INLINE`: `[Convert]::FromBase64String('<literal>')`, con o sin `[Text.Encoding]::<X>.GetString(...)`. Solo con un argumento literal |
| `transforms/concat.py` | `OT-CONCAT`: cadenas de literales entre comillas simples unidas con `+`. Una cadena entre comillas dobles con `$` o subexpresiones se marca como no resuelta |
| `transforms/varsub.py` | `OT-VARSUB`: sustituye `$x` en los puntos de uso solo si `$x` se asigna **una única vez** con un literal (o con un `OT-CONCAT` ya resuelto) y nunca se reasigna. Cualquier otro caso queda sin resolver |
| `transforms/format_detect.py` | `OT-FORMAT`: solo detecta el patrón y lo registra como `UnresolvedFragment` (cobertura `unsupported`, P7) |
| `engine.py` | Aplica las transformaciones por capas hasta un punto fijo. Cada decodificación abre una capa nueva que se vuelve a procesar. Límites: tamaño de entrada (`MAX_SCRIPT_SIZE_BYTES`, 1 MiB en `.env.example`), tamaño decodificado, profundidad máxima (3 capas) y número de iteraciones. Si se alcanza un límite, se registra en `limits_hit` y el análisis no se aborta |

**Principio:** el desofuscador **solo transforma texto**. Nunca evalúa expresiones arbitrarias, resuelve variables de entorno, accede a la red ni ejecuta nada. Ante cualquier duda, deja el fragmento sin resolver: la evaluación premia la recuperación verificable, no la cobertura especulativa.

## 5. Pruebas (TDD, antes de cada transformación)

1. **Equivalencia con la referencia del piloto:** P2 y P6 decodificados = `reference_recovery.decode_encoded_commands` = `reference/PILOT-P2_decoded` y `PILOT-P6_decoded`.
2. **Recuperación sobre el manifiesto:** en las filas con `deobfuscator_coverage ∈ {supported, partial}`, todas las `expected_recovered_strings` aparecen en algún artefacto o capa (P2, P3, P4, P6).
3. **No soportado:** P7 produce un `UnresolvedFragment` con `technique_hint = OT-FORMAT` y no inventa un artefacto.
4. **Comentarios:** el texto de los comentarios (P8) no se transforma ni se toma como código.
5. **Robustez:** Base64 inválido, UTF-16 truncado, comillas desbalanceadas y variables reasignadas producen fragmentos no resueltos, no excepciones.
6. **Límites:** entrada mayor que el máximo, más capas que la profundidad máxima y una "bomba" de decodificación generan `limits_hit`.
7. **Trazabilidad:** cada artefacto apunta a un rango cuyo texto original contiene el patrón transformado.
8. **Seguridad:** la prueba estática existente sigue pasando con el nuevo código.

## 6. Criterios de aceptación del incremento

- Las pruebas existentes (66 al cierre de la Fase 0B) y las nuevas pasan.
- Recuperación del 100% de las `expected_recovered_strings` en los casos `supported`/`partial` del piloto. Son pocos casos: esto es una prueba de regresión, no una métrica de investigación.
- P7 se reporta como no resuelto.
- Ningún componente ejecuta código, invoca PowerShell ni accede a la red.
- Ningún archivo del piloto v1 (prompt, configuración, ground truth, resultados, `reference_recovery.py`) se modifica.

## 7. Secuencia sugerida

| Paso | Contenido | Depende de |
|---|---|---|
| 1a | Contratos (`schemas/deobfuscation.py`) y `lexer.py` con sus pruebas | — |
| 1b | `OT-B64-ENCCMD` y `OT-B64-INLINE` | 1a |
| 1c | `OT-CONCAT` y `OT-VARSUB` | 1a |
| 1d | `engine.py`: capas, punto fijo y límites; caso combinado P6; detección de `OT-FORMAT` | 1b, 1c |
| 1e (siguiente incremento) | Reglas B01–B07 sobre el texto original y los artefactos, separando envoltorios añadidos (`LAUNCHER_ENCCMD`, `EXEC_WRAPPER_AMP`) de la ejecución funcional (B02) | 1d |

## 8. Decisiones que necesita el equipo

1. **Prefijos de `-EncodedCommand`:** PowerShell acepta abreviaturas del parámetro (`-enc`, `-e`, `-ec`…). Hay que decidir cuáles se reconocen. `-e` es ambiguo en otros contextos.
2. **Alcance de `OT-VARSUB`:** solo asignación única en el ámbito del script (lo propuesto), o también reasignaciones lineales sin ramas.
3. **Uso de los casos del piloto como fixtures de regresión**, declarándolo en la documentación (propuesto), o escribir fixtures nuevas independientes.
4. **Relación con `reference_recovery.py`:** mantenerlo congelado para el piloto (propuesto) y no hacerlo depender del nuevo servicio.
5. *(Resuelto el 2026-11-01: el responsable aprobó la desviación DEV-01, que permite iniciar la Fase 1A sin modelo seleccionado, tras el cierre formal de la Fase 0B; ver [methodology.md](methodology.md) §10.)* Recordatorio original: la [hoja de ruta](roadmap.md) condiciona la Fase 1 a la aprobación de la taxonomía y de los criterios. Este incremento no depende del modelo, pero sí de que el equipo acepte iniciarlo con la decisión de modelo pendiente.
