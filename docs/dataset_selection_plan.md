# Plan de selección, etiquetado y división del dataset — Fase 0A

**Proyecto:** PowerShell Insight AI
**Estado:** propuesta revisada, pendiente de aprobación del equipo. Ninguna muestra se ha escrito, generado ni descargado. Nada se congela hasta que el equipo lo apruebe.
**Base:** hallazgos de [dataset_audit.md](dataset_audit.md). Taxonomía aplicable: [behavior_taxonomy.md](behavior_taxonomy.md) (v0.2, B01–B07).

> **Revisión de la Fase 0A.** Esta versión incorpora las correcciones de una revisión técnica independiente: registro de equivalencia funcional entre original y variantes, taxonomía B01–B07, separación entre comportamiento, escenario y riesgo, 20–30 scripts base con división cercana a 50/50 por familias, mitigación del sesgo del generador, anotaciones de evidencia en JSON y revisión humana sin presuponer dos anotadores.

## 1. Principios

1. **El ground truth se construye, no se hereda.** Ninguna fuente pública trae pares original/ofuscado con etiquetas de comportamiento verificadas.
2. **Las etiquetas de comportamiento pertenecen al script original.** Una variante solo hereda esas etiquetas cuando su equivalencia funcional ha sido revisada (sección 3). Lo que añade la ofuscación se registra aparte (`obfuscation_techniques`, `added_operations`).
3. **Comportamiento, ofuscación y riesgo son ejes independientes**, cada uno con sus propios campos. La evaluación principal se centra en los comportamientos funcionales, no en una clasificación binaria de malware.
4. **La unidad de independencia experimental es la familia o el script base**, no la variante. Las variantes de un base, y los bases de una misma familia, nunca se separan entre desarrollo y prueba.
5. **No se inventan etiquetas, hashes, muestras ni revisiones** para completar cuotas. Si un estrato queda corto, se reporta así.
6. **Ninguna muestra se ejecuta.** Las muestras se almacenan como `.ps1.txt`. El material de terceros potencialmente peligroso no entra al repositorio: solo sus metadatos y hashes.

## 2. Composición propuesta

### 2.1 Scripts base

Meta inicial: **20–30 scripts base independientes**, ampliable si el etiquetado lo permite. Con sus variantes dan del orden de 60–100 muestras evaluables.

| Estrato | Origen | Cantidad orientativa | `scenario_type` esperado |
|---|---|---|---|
| **S1. Administrativos legítimos** | Escritos por el equipo o adaptados de documentación y repositorios con licencia clara (p. ej., Azure-Samples, ver [dataset_audit.md](dataset_audit.md)) | 9–13 | `administrative` |
| **S2. Simulaciones adversarias inertes** | Escritas por el equipo con dominios reservados (`example.com`, `.invalid`), rutas inexistentes y nombres ficticios | 9–13 | `adversarial_simulation` |
| **S3. Scripts públicos reales** (opcional) | Subconjunto corto de proyectos públicos con licencia, tomados del repositorio original y revisados en entorno aislado | 0–6 | según revisión manual |

- S1 debe incluir **comportamientos legítimos que coinciden con categorías del catálogo** (descargar un reporte, consultar procesos, probar conectividad, autenticarse en un servidor). Sin ellos no se puede demostrar que el sistema separa comportamiento de riesgo.
- Las simulaciones S2 son **escenarios de laboratorio**, no malware real. Usar dominios reservados o rutas inexistentes **no** convierte un script en seguro: el patrón de comportamiento sigue siendo el mismo y se etiqueta como tal.
- Objetivo de cobertura: cada categoría B01–B07 con positivos en desarrollo y en prueba. Si alguna (previsiblemente B04 o B07) queda con muy pocos positivos, se reporta como limitación y no se generaliza su resultado.

### 2.2 Familias

- `family_id` agrupa bases que comparten código o estructura (p. ej., dos versiones de un mismo cradle que cambian solo la URL, o scripts adaptados del mismo ejemplo público).
- La división desarrollo/prueba se hace **por familia**. Una familia con un solo base es válida.
- Antes de congelar se revisan casi-duplicados entre familias (similitud textual tras normalizar espacios, mayúsculas y literales); si dos familias resultan casi idénticas, se fusionan.

## 3. Equivalencia funcional entre original y variantes

La herencia de etiquetas solo es aceptable si hay justificación de que la transformación **conserva el comportamiento funcional de referencia**. Que una variante provenga de un original conocido **no basta** para declarar equivalencia.

### 3.1 Estados

| `semantic_equivalence_status` | Significado | Uso en el análisis |
|---|---|---|
| `not_applicable` | Es el original (`v0`) | Referencia |
| `reviewed_static` | Una revisión estática documentada no encontró diferencias funcionales respecto del original | **Comparación principal** |
| `partial` | La variante conserva el comportamiento funcional, pero añade operaciones (p. ej., envoltorio `IEX`) o hay fragmentos cuya equivalencia no pudo revisarse | Análisis separado, reportado por estrato |
| `unverified` | No se ha revisado (o no puede revisarse estáticamente) | Excluida de la comparación principal hasta revisarse |
| `behavior_altered` | La transformación cambió el comportamiento funcional (rompe, omite o añade lógica funcional) | Excluida; se documenta la causa |

### 3.2 Métodos de revisión (`equivalence_review_method`)

| Valor | Descripción |
|---|---|
| `none` | Sin revisión |
| `decoded_text_comparison` | Se decodifica o resuelve estáticamente la variante (fuera del sistema evaluado, con herramienta de referencia o a mano) y se compara el texto normalizado con el original |
| `manual_static_review` | Lectura manual de la variante contra el original, siguiendo la lista de comprobación de esta sección |
| `token_diff_review` | Comparación de tokens o del AST obtenido sin ejecutar, con revisión de las diferencias |

Cada revisión deja en `equivalence_notes` qué se comparó y qué diferencias se encontraron.

### 3.3 Operaciones introducidas por la ofuscación

- Los envoltorios de ejecución añadidos por la herramienta (`IEX`, `&`, `.Invoke()`, lanzadores `powershell -enc`) se registran en `added_operations` (p. ej., `EXEC_WRAPPER_IEX;LAUNCHER_ENCCMD`).
- **No** se añade B02 por estas operaciones: B02 se reserva a la ejecución dinámica del original ([behavior_taxonomy.md](behavior_taxonomy.md)).
- Una variante con operaciones añadidas que no alteran la lógica funcional queda, como máximo, en `partial`, salvo que el equipo decida explícitamente que un tipo concreto de envoltorio se considera neutro y lo documente en [methodology.md](methodology.md) antes de congelar el conjunto de prueba.

### 3.4 Limitación

La equivalencia completa entre dos programas no puede demostrarse en general mediante análisis estático. `reviewed_static` significa "revisado sin encontrar diferencias", no "probado equivalente". Esta limitación se reportará en el informe.

## 4. Variantes y generador

### 4.1 Códigos de técnicas de ofuscación

Lista inicial, ampliable:

| Código | Técnica | Cobertura prevista del desofuscador |
|---|---|---|
| `OT-B64-ENCCMD` | Base64 UTF-16LE con `-EncodedCommand` | `supported` |
| `OT-B64-INLINE` | `FromBase64String` en línea | `supported` |
| `OT-CONCAT` | Concatenación de literales | `supported` |
| `OT-VARSUB` | Sustitución de variables con valores literales | `supported` |
| `OT-FORMAT` | Operador de formato `-f` con reordenamiento | `unsupported` (por ahora) |
| `OT-IO-TOKEN`, `OT-IO-STRING`, `OT-IO-ENCODING` | Familias de Invoke-Obfuscation | `unsupported` o `partial` |

### 4.2 Variantes por script base

| Variante | Técnica | Generador | Cobertura del desofuscador |
|---|---|---|---|
| `v0` | Original sin ofuscar (control) | — | `none` |
| `v1` | Base64 / `-EncodedCommand` | Generador propio | `supported` |
| `v2` | Concatenación de literales | Generador propio | `supported` |
| `v3` | Sustitución de variables literales | Generador propio | `supported` |
| `v4` | Combinada (p. ej., v2 + v1) | Generador propio | `supported` o `partial` |
| `v5` | Técnica no soportada (TOKEN/STRING/ENCODING de Invoke-Obfuscation, o `-f` escrito a mano) | Invoke-Obfuscation CLI en entorno aislado, o manual | `unsupported` |

No hace falta generar todas las variantes de cada base. Se exige que **cada técnica tenga al menos 8 bases** y que el **estrato no soportado tenga al menos 8 muestras**, sumando desarrollo y prueba. Con una división 50/50, el número por técnica en prueba será pequeño: los resultados por técnica se presentan como exploratorios.

Ejemplo de cálculo: 24 bases × (v0 + 2 soportadas + v5 en la mitad de los casos) ≈ 24 + 48 + 12 = **84 muestras**.

### 4.3 Generador propio y mitigación de sesgo

Riesgo: si el generador y el desofuscador usan exactamente los mismos patrones, la configuración C resultaría favorecida artificialmente. Mitigaciones:

1. El generador es un script Python **determinista** (semilla fija) que solo transforma texto y registra `transform_params` y `expected_recovered_strings`. Se implementa en la Fase 1.
2. Para cada técnica soportada se definen dos **conjuntos de variantes sintácticas** (`syntax_pool`):
   - `dev`: formas usadas para desarrollar y depurar el desofuscador (p. ej., concatenación con `+`).
   - `heldout`: formas equivalentes reservadas que **no se usan durante el desarrollo** (p. ej., `-join`, `[string]::Concat`, comillas simples/dobles mezcladas, `-EncodedCommand` abreviado como `-enc`/`-e`).
   La lista concreta se fija y se guarda fuera del alcance de quien desarrolla las reglas, en la medida en que el equipo lo permita; si no es posible, se documenta.
3. Se incluyen técnicas deliberadamente no soportadas (`v5`).
4. Invoke-Obfuscation se mantiene como generador candidato de variantes adicionales de scripts **inertes y propios**, en entorno aislado.
5. Cuando sea viable, se añade un conjunto pequeño de ejemplos públicos revisados (S3).
6. Todos los resultados se reportan **por tipo de transformación**.

### 4.4 Evaluación controlada y de generalización

| Grupo (`evaluation_group`) | Contenido | Qué permite afirmar |
|---|---|---|
| `controlled` | Bases de prueba con variantes `v0`–`v4` del conjunto sintáctico `dev`, con comportamiento y transformación conocidos | Efecto de la desofuscación en condiciones conocidas |
| `generalization` | Variantes `heldout`, `v5` (no soportadas) y scripts S3 | Si el efecto se mantiene ante formas no vistas o de procedencia externa |
| `pilot` | Casos del piloto ([pilot_plan.md](pilot_plan.md)) | Solo viabilidad del modelo; no entra en la evaluación |

Los resultados de `controlled` y `generalization` se reportan por separado. Si se presenta un agregado, se acompaña de los resultados por grupo y de la explicación de sus diferencias.

## 5. División desarrollo / prueba

1. **El piloto está completamente separado** (`split = pilot`): sus casos no se reutilizan en desarrollo ni en prueba, y ninguna familia de prueba puede derivar de un caso del piloto.
2. **Primero se dividen las familias**, después se generan las variantes.
3. Proporción inicial: **cercana a 50/50** entre desarrollo y prueba, estratificada por estrato (S1/S2/S3) y ajustada para que cada comportamiento tenga positivos en ambos conjuntos.
4. Los ejemplos que se incluyan en los prompts solo pueden venir de desarrollo.
5. El conjunto de prueba se **congela** (`review_status = frozen`) **antes** de los ajustes definitivos de prompts y reglas. Cualquier cambio posterior se documenta en [methodology.md](methodology.md) con su motivo.
6. Con 20–30 familias, los resultados se describen como **exploratorios**, no como conclusiones estadísticas generales.

## 6. Evidencias y anotaciones

El manifiesto CSV registra metadatos por muestra. Las evidencias, que pueden ser varias por etiqueta y abarcar varias líneas, se registran en un archivo JSON aparte, siguiendo la plantilla [`datasets/metadata/annotations_template.json`](../datasets/metadata/annotations_template.json). El manifiesto enlaza a ese archivo mediante `annotation_ref`.

Cada evidencia indica su procedencia (`evidence_source`):

| Valor | Significado | Líneas referidas a |
|---|---|---|
| `original` | Código del original (`v0`) | El archivo original |
| `obfuscated_variant` | Texto literal de la variante ofuscada | El archivo de la variante |
| `recovered` | Contenido recuperado por el desofuscador | El artefacto recuperado identificado por `transformation_id` |

Las evidencias de referencia (ground truth) se registran sobre el original. Las evidencias de tipo `recovered` se usarán para verificar las salidas del sistema en las Fases 1–2. `verification_status` distingue evidencia pendiente, verificada literalmente, verificada por revisión y rechazada.

## 7. Manifiesto: campos

Plantilla: [`datasets/metadata/manifest_template.csv`](../datasets/metadata/manifest_template.csv). Una fila por muestra (original o variante).

| Campo | Descripción | Valores |
|---|---|---|
| `sample_id` | Identificador único de la muestra | `S-0001` |
| `base_script_id` | Script base del que proviene | `BASE-001` |
| `family_id` | Familia de scripts similares | `FAM-001` |
| `variant_id` | Variante | `v0`…`v5` |
| `is_original` | ¿Es el original sin ofuscar? | `true` / `false` |
| `split` | División experimental | `pilot` / `dev` / `test` |
| `evaluation_group` | Grupo de evaluación | `controlled` / `generalization` / `pilot` |
| `stratum` | Estrato del base | `S1` / `S2` / `S3` |
| `scenario_type` | Tipo o intención del escenario | `administrative`, `adversarial_simulation`, `external_reviewed`, `unknown` |
| `source_type` | Origen | `own_administrative`, `own_inert_simulation`, `public_administrative`, `public_offensive`, `generated_variant` |
| `source_name`, `source_url` | Fuente y URL de procedencia | texto / URL |
| `source_license` | Licencia de la fuente | SPDX o `unknown` |
| `provenance_notes` | Notas de procedencia (commit, fecha, ruta original) | texto |
| `sha256` | Hash del archivo, **solo si el archivo existe** | hex o vacío |
| `stored_in_repo` | ¿El archivo está en el repo? | `true` / `false` |
| `file_location_ref` | Ruta en el repo o referencia externa | texto |
| `size_bytes`, `line_count` | Tamaño del archivo | entero |
| `obfuscation_techniques` | Técnicas aplicadas (sección 4.1), separadas por `;` | `OT-B64-ENCCMD;OT-CONCAT` |
| `transform_tool` | Herramienta | `own_generator`, `invoke_obfuscation`, `manual`, `none` |
| `transform_params` | Parámetros exactos (semilla o comando CLI) | texto |
| `syntax_pool` | Conjunto sintáctico del generador | `dev`, `heldout`, `na` |
| `added_operations` | Operaciones introducidas por la ofuscación, separadas por `;` | `EXEC_WRAPPER_IEX` o vacío |
| `deobfuscator_coverage` | Cobertura esperada del desofuscador | `none`, `supported`, `partial`, `unsupported` |
| `expected_recovered_strings` | Cadenas clave que deberían recuperarse, separadas por `;` | texto |
| `semantic_equivalence_status` | Estado de equivalencia (sección 3.1) | `not_applicable`, `reviewed_static`, `partial`, `unverified`, `behavior_altered` |
| `equivalence_review_method` | Método de revisión (sección 3.2) | `none`, `decoded_text_comparison`, `manual_static_review`, `token_diff_review` |
| `equivalence_notes` | Qué se comparó y qué diferencias hubo | texto |
| `behavior_labels` | Resumen de comportamientos de referencia, separados por `;` | `B01;B05` |
| `label_basis` | Fundamento de las etiquetas de comportamiento | `design`, `manual_review`, `inherited_reviewed` |
| `annotation_ref` | Archivo JSON con las evidencias | ruta |
| `risk_label` | Valoración de riesgo sustentada | `benign`, `suspicious`, `high_risk`, `unknown` |
| `risk_certainty` | Certeza de la valoración | `high`, `medium`, `low` |
| `risk_basis` | Fundamento de la valoración | `design`, `manual_review`, `source_provenance`, `author_label` |
| `annotator_1`, `annotator_2` | Iniciales de quienes etiquetaron (`annotator_2` vacío si no hubo segunda revisión) | texto |
| `agreement` | Coincidencia entre anotadores, solo si hubo segunda revisión real | `full`, `partial`, `disagree`, vacío |
| `review_status` | Estado | `draft`, `annotated`, `reviewed`, `frozen` |
| `known_limitations` | Limitaciones conocidas | texto |
| `notes` | Notas libres | texto |

**Valoración de riesgo:**
- `benign`: propósito administrativo o legítimo claro.
- `suspicious`: comportamientos compatibles con abuso, sin propósito legítimo evidente.
- `high_risk`: combinación de comportamientos característica de abuso (p. ej., descargar y ejecutar contenido remoto). **No significa malware verificado.**
- `unknown`: no es posible sustentar una valoración.

Una simulación adversaria se valora por el patrón que contiene, con `scenario_type = adversarial_simulation` y `risk_basis = design`; no se registra como malware confirmado. La etiqueta "malicioso confirmado" no se usa para simulaciones; para muestras externas solo sería admisible con procedencia verificable y revisión manual, y se documentaría en `notes`.

Respecto de la versión anterior: `behavior_evidence` se sustituye por `annotation_ref`; `maliciousness_*` pasa a `risk_*`; `public_malicious` pasa a `public_offensive` (la procedencia ofensiva no prueba maliciosidad); se añaden `family_id`, `evaluation_group`, `scenario_type`, `syntax_pool`, `added_operations` y los campos de equivalencia.

## 8. Guía de etiquetado y revisión humana

1. **Etiquetar el original (`v0`)**, nunca directamente la variante.
2. Las variantes con `reviewed_static` copian `behavior_labels` y `risk_*` del original (`label_basis = inherited_reviewed`); con otros estados, se copian como referencia provisional pero la muestra se trata según la sección 3.1.
3. **Etiquetar lo que el código hace**, con evidencia localizada en el archivo de anotaciones.
4. **Ofuscar no cambia la valoración de riesgo.** Un script administrativo codificado en Base64 sigue siendo `benign`.
5. **Ante la duda, no etiquetar:** usar `unknown`, bajar la certeza y documentarlo en `known_limitations`.

**Revisión humana:**

- El escenario por defecto es que **una sola persona** anote. En ese caso se documenta como limitación y se compensa con criterios escritos, evidencia trazable y una segunda pasada propia separada en el tiempo (registrada como tal, no como segundo anotador).
- Si otra persona del equipo revisa de forma independiente un subconjunto, se registra en `annotator_2` y `agreement`.
- El acuerdo solo se cuantifica si hubo una segunda revisión real. El kappa de Cohen por categoría solo se calcula si hay suficientes casos doblemente anotados y positivos de esa categoría para que sea interpretable; si no, se reporta el acuerdo de forma descriptiva (número de coincidencias y desacuerdos) o se indica que no aplica.
- No se registran revisiones ni porcentajes de concordancia que no hayan ocurrido.

## 9. Uso de cada fuente

| Fuente | Uso en el dataset |
|---|---|
| Scripts propios (S1 y S2) | **Núcleo del conjunto.** Comportamiento conocido por diseño |
| Azure-Samples/azure-docs-powershell-samples | Candidata para S1 (administrativos reales, licencia MIT), tras revisión y adaptación |
| Invoke-Obfuscation | Generar `v5` sobre scripts propios inertes, en entorno aislado |
| Revoke-Obfuscation | Referencia metodológica; el PowerShellCorpus no se descarga por ahora (sección 10) |
| Fa2y / MPSD | Opcional para S3: ≤ 6 scripts cortos, revisados en entorno aislado, preferiblemente tomados del repositorio original con licencia clara |

## 10. Decisiones

### Resueltas en esta revisión

- Taxonomía de **siete comportamientos funcionales (B01–B07)**; B08 retirado y no reutilizado.
- B02 restringido a la ejecución dinámica funcional del original; regla B01/B06; `Get-Credential` para autenticarse no es B07.
- Registro de equivalencia funcional con cinco estados; solo `reviewed_static` entra en la comparación principal.
- Separación entre comportamiento, `scenario_type` y `risk_label`.
- 20–30 bases, división cercana a 50/50 por familias, piloto separado.
- Evidencias en JSON aparte del manifiesto.
- Revisión humana sin presuponer dos anotadores.
- **Por ahora no se descarga el PowerShellCorpus.** Los administrativos (S1) se escriben a mano o se adaptan de fuentes con licencia clara. Se reconsiderará solo si faltan administrativos realistas.
- **El piloto inicial no incorpora scripts públicos reales (S3)**: solo usa scripts propios.

### Pendientes antes de la Fase 0B

1. Decidir si el estrato **S3** se incluye después del piloto, en los conjuntos de desarrollo y prueba, y quién lo revisa.
2. Definir el **entorno aislado** (VM Linux, WSL o Colab) para generar `v5` y, en su caso, inspeccionar S3.
3. Confirmar el **tope de tamaño** por script (propuesta: ≤ 150 líneas).
4. Fijar las listas sintácticas `dev` y `heldout` del generador.
5. Decidir si algún tipo de envoltorio añadido se considera neutro (sección 3.3).
6. Decidir el tratamiento de las llamadas a API de nube respecto de B06.
