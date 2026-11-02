# Fase 1A — Aprobación técnica y cierre formal

**Estado:** **APROBADA TÉCNICAMENTE Y CERRADA FORMALMENTE** por el responsable dentro del subconjunto funcional documentado, mediante su autorización expresa en esta conversación. La Fase 1B no está autorizada ni iniciada; el responsable revisará y publicará personalmente los cambios.

**Fecha del registro documental:** 2026-11-02, según el contexto de la sesión. Preparado con asistencia de IA. No se atribuye una fecha distinta de revisión humana ni se registra firma.

**Responsable:** Responsable del proyecto, identificado por ese rol y por la autorización recibida; no se dispone de un nombre personal verificado. Fuente de aprobación: mensaje «Aprobación y cierre formal de la Fase 1A», que declara «Apruebo técnicamente la Fase 1A dentro del subconjunto funcional documentado». No equivale a validación independiente del código.

La autorización reconoce las 271 pruebas de auditoría y los cinco defectos corregidos, acepta las limitaciones del reconocedor, mantiene OT-FORMAT sin recuperación y la prohibición de ejecutar scripts, conserva la evidencia de la Fase 0B y reconoce la preparación para integrarse con futuras reglas de la Fase 1B. Antes de registrar este cierre se realizó únicamente la comprobación puntual CRLF/LF descrita en las secciones 7 y 9, sin repetir la auditoría del motor.

## 1. Objetivo y alcance

Recuperar texto y bytes de entradas PowerShell no confiables mediante transformaciones estáticas, deterministas, acotadas y trazables. La API recibe texto; conserva L0 y devuelve artefactos separados, sin reescribir ni ejecutar scripts. El alcance exacto y los ejemplos están en [deobfuscator.md](deobfuscator.md).

Se revisaron todos los módulos nuevos del servicio, su esquema, las pruebas y fixtures de desofuscación y la demo. No se añadieron técnicas nuevas, reglas B01–B07, riesgos, Ollama, FastAPI, React ni evaluación A/B/C. La Fase 1B permanece sin iniciar.

## 2. Componentes implementados

| Componente | Responsabilidad y resultado de revisión |
|---|---|
| `backend/app/services/deobfuscation/__init__.py` | API pública `deobfuscate`, independiente del servidor web |
| `lexer.py` | Tokens y diagnósticos; comentarios y cadenas opacos; offsets de caracteres |
| `expressions.py` | Gramática acotada y árbol previo a la recuperación; no despacha métodos |
| `transforms.py` | Base64 estricto, conversiones explícitas de bytes y concatenación pura |
| `variables.py` | Asignación única local, dependencias y exclusión conservadora de efectos y alias |
| `encoded_command.py` | Lanzador literal, parámetros permitidos y límites de argumentos |
| `budget.py` | Cotas de trabajo y volumen; interrupción controlada |
| `engine.py` | Orquestación, registro de artefactos, diagnósticos y capas hijas |
| `backend/app/schemas/deobfuscation.py` | Contratos Pydantic, trazabilidad, estados y límites configurables |
| `backend/tests/deobfuscation/` | Cuatro módulos de pruebas, inicializador y tres archivos de fixtures |
| `experiments/demo_deobfuscation.py` | Demo Python inerte y portable, sin persistencia de resultados |

La separación es suficiente para este alcance y no requiere una refactorización extensa. Se reutiliza únicamente el enum de técnicas del esquema existente; no se consumen respuestas del LLM. Se usan biblioteca estándar y Pydantic, ya declarado en `backend/requirements-pilot.txt`; no se instalaron dependencias. Las entradas inválidas de API generan TypeError/ValidationError; sintaxis no soportada y límites generan resultados estructurados.

Las rutas lógicas son metadatos y no se abren. La demo resuelve sus imports desde `__file__`; una prueba la ejecuta desde un directorio ajeno. No depende del directorio actual ni de una ruta fija de Windows.

## 3. Técnicas soportadas

| Técnica | Subconjunto |
|---|---|
| OT-B64-ENCCMD | Lanzador literal con `-EncodedCommand`/`-enc`, argumento final separado y literal, Base64 estándar y UTF-16LE estricto; abre capa hija |
| OT-B64-INLINE | `Convert.FromBase64String` y `Encoding.GetString` textualmente permitidos, con Unicode/BigEndianUnicode/UTF8/ASCII; bytes sin encoding explícito permanecen bytes |
| OT-CONCAT | Cadenas literales, paréntesis y variables admitidas; solo concatenación de cadenas |
| OT-VARSUB | Nombres ASCII simples, asignación única anterior al uso, capa local y barreras de efectos |
| OT-FORMAT | Detección y diagnóstico `unsupported`; no resolución |

Los reconocimientos describen forma sintáctica, sin probar qué ejecutable o tipo resolvería PowerShell en una sesión real. `semantic_equivalence = not_claimed` siempre.

## 4. Resultados de recuperación por caso

Inspección estática de las entradas históricas, leídas como datos; nunca ejecutadas.

| Caso | Estado del motor | Capas / transformaciones / no resueltos | Resultado comprobado |
|---|---|---|---|
| P2 | complete | 2 / 1 / 0 | Capa hija exactamente igual a la referencia controlada y al recuperador histórico; conserva el pipeline Get-Process |
| P3 | partial | 1 / 9 / 6 | `Invoke-WebRequest`, `https://example.com/report.csv` y `report.csv`; no calcula Join-Path ni inventa el destino o su propagación posterior |
| P4 | complete | 1 / 6 / 0 | Tres valores literales con definición y uso: ruta CurrentVersion/Run, PilotLabUpdater y ruta inerte del ejecutable; sin afirmar persistencia efectiva |
| P6 | partial | 2 / 3 / 1 | Capa hija exactamente igual a la referencia y al recuperador histórico; concatena Net.WebClient y la URL. New-Object queda explícitamente fuera de la gramática |
| P7 | partial | 1 / 7 / 11 | Tres transformaciones OT-FORMAT unsupported; ninguna cadena recuperada |

El cambio de estado de P6 de `complete` a `partial` corrige un diagnóstico del motor nuevo. La decodificación exacta permanece igual y no se recalculan las métricas del piloto v1. `complete` significa que terminó el reconocimiento sin incidencias detectadas en este subconjunto; no significa comprensión completa de PowerShell.

## 5. Restricciones y limitaciones

El motor no implementa el parser oficial ni análisis de flujo, alcanzabilidad, ámbitos generales, interpolación, arrays, casts, compresión, cifrado, reflexión o métodos arbitrarios. No consulta variables de entorno ni recupera contenido remoto. Las líneas LF y CRLF están cubiertas; la segmentación con separadores exclusivamente CR no está garantizada.

Se excluyen conservadoramente escrituras con nombres no admitidos, reasignaciones, asignaciones compuestas, bloques y contextos con posibles efectos. Se sacrifica cobertura para evitar valores atribuidos indebidamente. Los bytes con codificación incompatible conservan su recuperación binaria sin adivinar texto. Solo EncodedCommand crea capas de script; el texto inline sigue siendo dato.

Las cotas por defecto incluyen entrada de 1 MiB, valor de 256 KiB, acumulado de 2 MiB, 512 transformaciones, profundidad de capas 3, profundidad de expresiones 24, 128 términos, 50 000 tokens, 4 000 000 unidades de trabajo y 128 diagnósticos. El esquema impone techos también a configuraciones del llamador. El acumulado no representa todo el overhead Python/JSON. El presupuesto es determinista y no garantiza una latencia de reloj ni aislamiento de proceso.

Las pruebas sintéticas propias permiten cambiar nombres, valores, composición y contexto sin recurrir al piloto. Son pruebas de desarrollo y regresión, no un conjunto ciego ni una medición de generalización experimental. Los modelos congelados tienen listas mutables: un payload modificado debe revalidarse antes de confiar en él.

## 6. Seguridad y trazabilidad

Se revisó el recorrido entrada → lexer → árbol permitido → transformaciones puras → registros/capas. No hay evaluación Python, ejecución PowerShell, subprocesos, despacho dinámico, acceso a archivos o conexiones en ese recorrido. El contenido decodificado vuelve únicamente al reconocedor acotado. No se ejecutaron muestras ni se realizaron nuevas inferencias.

Las pruebas inspeccionan imports y llamadas del AST y bloquean procesos, sockets y lectura de archivos durante recuperaciones de texto adversario inerte. Los imports del servicio se limitan a biblioteca estándar, módulos internos y esquemas. No hay lecturas de referencias, ground truth, respuestas Qwen o reglas con cadenas de P1–P8 en producción. Las referencias y el recuperador histórico se usan como oráculos únicamente en pruebas.

Base64 malformado, padding incorrecto, Unicode incompatible, entradas grandes, límites de tokens/expansión/trabajo, ciclos de variables y sintaxis opaca devuelven resultados controlados. Un límite conserva los artefactos previos y el original aceptado; una entrada rechazada por tamaño o Unicode inválido se omite de la salida para no duplicarla. El original del llamador no se modifica.

Los offsets cuentan caracteres Unicode de Python, con final exclusivo; líneas y columnas comienzan en 1. Cada fragmento es una porción exacta de su capa. L0 se conserva y se verifica por SHA-256; las capas hijas tienen productor, profundidad y procedencia `deobfuscator_recovered`. Un fragmento en L1/L2 usa coordenadas locales y un ancla `root_source` al argumento Base64 de L0: no se presenta como texto literal del original.

Se verificaron ASCII, Unicode y CRLF, fragmentos iguales en ubicaciones distintas, variables dependientes, dos decodificaciones anidadas y cambios de longitud entre origen y resultado. Los IDs y el JSON son repetibles con igual entrada/configuración. Las dependencias preceden al consumidor; el contrato rechaza ciclos, referencias inexistentes, rangos falsos, fragmentos alterados y relaciones de capas inconsistentes. No se encontró una ruta de ejecución de la entrada; esta revisión y estas pruebas no constituyen una demostración formal de seguridad de Python o Pydantic.

## 7. Resultados finales de pruebas

| Conjunto | Aprobadas |
|---|---:|
| Anteriores a la Fase 1A | 82 |
| Implementación inicial de la Fase 1A | 159 |
| Regresiones y variantes sintéticas de auditoría | 30 |
| Regresiones de filtros Git CRLF/LF para el cierre | 3 |
| **Total final** | **274** |

La auditoría aprobada por el responsable registró **271 passed in 1.02s**. Tras el ajuste puntual CRLF/LF, la suite completa registró **274 passed in 5.36s**, sin fallos ni omisiones. Tiempos observados del entorno local, no benchmarks. Las 30 pruebas de auditoría cubren escrituras con alias (8), asignaciones compuestas adicionales (2), separadores de argumentos (5), diagnóstico de expresiones no soportadas (3), corrupción de bytes parciales (4), estados globales incoherentes (2), capas/variables Unicode (3), fragmentos repetidos (1), ausencia de I/O (1) y demo desde otro directorio (1).

Las tres nuevas regresiones en `backend/tests/test_repository_line_endings.py` prueban 18 archivos con hashes históricos registrados usando `git -c core.autocrlf=false|true|input cat-file --filters HEAD:ruta`. Fallaron con los atributos anteriores y pasaron con las excepciones acotadas. Se usan blobs de HEAD y los atributos actuales del árbol de trabajo; `-c` no cambia la configuración persistente. Es una comprobación de filtros Git, **no un checkout nuevo ni una ejecución en otro sistema operativo**. Estas pruebas requieren el ejecutable Git; el motor no añade esa dependencia.

Comando ejecutado desde la raíz, con un directorio temporal nuevo por ejecución:

```powershell
$closureTemp = Join-Path $env:TEMP ('powershell-insight-closure1a-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests --basetemp "$closureTemp" --tb=short
```

Es una ejecución de Python; los textos PowerShell son datos. Los temporales se crearon fuera del repositorio y se conservaron. No se eliminaron archivos. También se comprobaron `git diff --check`, índice sin staging, reglas de ignorados, referencias locales y ausencia de temporales/cachés de pruebas en el repositorio, excluyendo el entorno `.venv`.

## 8. Defectos encontrados y correcciones

| ID | Defecto reproducido | Corrección mínima y regresión |
|---|---|---|
| A1 | `$parcel='amber'; $local:parcel='violet'; Write-Output $parcel` recuperaba el valor anterior; variantes con llaves/ámbitos podían eludir la política. `%=` y `??=` tampoco invalidaban todos los usos previos conforme al contrato de asignación única | Deshabilitar bindings de la capa ante escrituras con nombre no admitido e incluir los operadores omitidos en la exclusión. Diez casos |
| A2 | Se decodificaba `-enc'BASE64'` y otras formas pegadas, o separadas solo por continuación escapada, como si fueran argumentos independientes | Exigir separación de argumentos por whitespace real tras quitar continuaciones. Cinco negativos |
| A3 | El fallo al analizar paréntesis de argumentos se omitía y podía devolver `complete` para una expresión no soportada | Registrar un fragmento no resuelto; conservar solo recuperaciones interiores válidas. Tres casos; P6 ahora partial |
| A4 | El esquema aceptaba una transformación parcial de bytes sin bytes, con Base64 inválido, sin verificación o con tipo incoherente | Validar contenido binario, tipo y verificación para partial. Cuatro payloads corruptos |
| A5 | El esquema admitía `complete` junto a no resueltos o límites alcanzados | Rechazar la contradicción en la validación del resultado. Dos payloads corruptos |

Antes de corregir, 20 de los 27 casos iniciales de auditoría fallaron y 7 pasaron; después pasaron los 27. Se añadieron tres comprobaciones de trazas/I/O/portabilidad y se ejecutó la suite completa con los 271 casos aprobados. A4/A5 eran debilidades de validación de payloads: no se observó que el motor emitiera esas combinaciones corruptas.

Archivos alterados durante esta auditoría: `backend/app/schemas/deobfuscation.py`, `backend/app/services/deobfuscation/variables.py`, `encoded_command.py`, `engine.py`, `backend/tests/deobfuscation/test_audit_regressions.py` (nuevo), [deobfuscator.md](deobfuscator.md) y este registro (nuevo). No se cambió el parser ni se amplió su gramática.

## 9. Integridad de la Fase 0B y de Git

Los hashes de todos los archivos existentes al inicio de la auditoría se compararon después: entonces solo cambiaron los cuatro módulos indicados y la documentación del motor. Para el cierre se comparó nuevamente el inventario previo: solo cambiaron `.gitattributes`, `README.md`, `docs/roadmap.md`, `docs/deobfuscator.md` y este registro; se añadió la prueba de filtros. No falta ningún archivo y el motor no se modificó durante este cierre. Se conservan byte por byte muestras, manifiestos, anotaciones v0.1/v0.2, revisiones, resultados, prompts, configuración, recuperador histórico y acta de la Fase 0B. Permanecen las etiquetas B01–B07, riesgos, DEV-01, DEV-02 y DEC-01 y sus limitaciones metodológicas.

Se comprobaron las 10 muestras del manifiesto (SHA-256 y tamaño), las dos referencias decodificadas, las 6 entradas de `pilot-v1_20261101T001806Z.SHA256SUMS`, el hash de v0.1 y el de la revisión en `derivation.json`. No se regeneraron resultados ni métricas. Las dos fixtures propias mantienen sus hashes y LF.

El cambio inicial de esta fase en `.gitattributes` añadió dos patrones bajo `backend/tests/deobfuscation/fixtures/`: texto `.ps1.txt` y `.json` con LF. Evita cambios en los hashes de fixtures debidos a finales de línea. Para este cierre se añadieron excepciones específicas de los artefactos históricos afectados; no se reescribieron archivos ni se ejecutó renormalización.

**Diagnóstico puntual CRLF/LF:** los hashes históricos identifican una mezcla de archivos CRLF y LF, mientras Git almacena sus blobs con LF. Antes del ajuste, aplicar los filtros a los ocho archivos de hash críticos produjo seis discrepancias con `core.autocrlf=false` o `input` y tres con `true`. Afectaban a anotaciones v0.1, resultados v1, CSV o revisión derivada según la configuración. Por tanto, sí podían fallar `test_v02_references_the_unchanged_v01`, la comprobación de propuesta v0.2 o `test_historical_results_match_recorded_hashes` al obtener archivos desde Git, aunque el contenido JSON siguiera siendo equivalente.

**Corrección mínima autorizada:** excepciones `text eol=crlf` para las anotaciones v0.1/v0.2, JSON/JSONL de la ejecución v1 exacta y JSON de su carpeta derivada exacta; `text eol=lf` para su CSV, SHA256SUMS y la revisión de evidencias v2. Se mantienen LF para muestras y fixtures. Así Git conserva sus blobs normalizados y sus filtros reconstruyen los finales de línea de los archivos cuyos hashes se registraron. Las excepciones no abarcan experimentos futuros.

Los filtros ahora reproducen los 18 hashes registrados comprobados con `false`, `true` e `input`: seis resultados v1, anotaciones v0.1, revisión de evidencias y diez muestras del manifiesto. Por ejemplo, v0.1 mantiene `f27e3b8cd70a8dd0522a7eeee760651a6eaf1cd0eb5d00fcad0c0bc5f7b245c5` al aplicar filtros; su blob LF conserva `940039c831a7dd402a4ce3b8489b99b574d94700aa285f5cb31dbe5610fb4773`. La identidad binaria se comprueba sobre archivos materializados, no sobre el blob normalizado. Todos los archivos históricos locales mantienen sus bytes y hashes anteriores. **No se creó ni se verificó un checkout nuevo.** La comprobación presupone atributos normales del repositorio, sin overrides externos.

**Pendiente residual, separado del checkout:** `experiments/run_pilot.py:evaluate` escribe JSON/JSONL con la traducción de saltos de línea del sistema operativo. Regenerar derivados en un sistema con LF puede producir el mismo contenido funcional y métricas, pero otros bytes frente a los históricos CRLF. En particular, `test_evaluate_into_new_dir_reproduces_historical_metrics` compara también hashes binarios de `evaluated_runs.jsonl`; esa comparación puede fallar fuera de Windows aunque coincidan los datos. No se ejecutó Linux ni se modificaron el evaluador, las pruebas históricas, los hashes o la metodología para resolverlo. Queda pendiente un trabajo autorizado que defina una serialización binaria explícita para nuevos derivados, conservando las referencias históricas y sin debilitar sus comprobaciones. La portabilidad funcional del motor y la identidad binaria de derivados regenerados son criterios distintos.

Rama `develop`, índice vacío de cambios y trabajo local sin staging. Las cuatro diferencias de contenido respecto a HEAD en archivos ya versionados son las previstas para la implementación: `.gitattributes`, `README.md`, `docs/architecture.md` y `docs/roadmap.md`. El servicio, esquema, pruebas, demo y documentos nuevos siguen sin seguimiento hasta la revisión del responsable. No se ejecutaron add, commit, push, merge, rebase ni operaciones destructivas.

`.gitignore` excluye `.venv`, `__pycache__` y `.pytest_cache`; se comprobó con `git check-ignore`. No hay temporales sueltos ni cachés de pruebas dentro del repositorio fuera de `.venv`. Git avisa de falta de acceso al ignore global del usuario; las reglas locales se verificaron y el inventario explícito de archivos no depende de ese ignore global. También avisa de futuras conversiones LF/CRLF en documentos generales; no se modificaron sus atributos.

## 10. Criterios de aceptación cumplidos y pendientes

| Criterio | Estado |
|---|---|
| Cuatro técnicas recuperadas dentro del subconjunto y -f diagnosticado | Cumplido |
| Original preservado, artefactos/dependencias/rangos verificables | Cumplido |
| Determinismo y límites efectivos; sin ejecución ni I/O de la entrada | Cumplido en revisión y pruebas |
| P2/P6 exactos, P3/P4 sin valores inventados, P7 sin resolución | Cumplido |
| Suite completa, demo portable y regresiones de defectos | Cumplido: 274 pruebas finales, incluidas las 271 de la auditoría aprobada |
| Datos históricos locales, resultados y decisiones de Fase 0B intactos | Cumplido |
| Reconstrucción de hashes históricos mediante filtros de checkout | Corregida y verificada: 18 archivos, tres valores de core.autocrlf; sin checkout nuevo |
| Identidad binaria de derivados regenerados en otros sistemas | Pendiente separado: serialización dependiente del sistema; no se modificó el evaluador |
| Documentación y cambios listos para revisión, Git sin staging | Cumplido |
| Aprobación técnica y cierre formal por el responsable | Cumplido mediante autorización expresa de esta conversación; sin nombre o firma inventados ni validación independiente |
| Inicio de Fase 1B | No autorizado y no iniciado |

No quedan defectos reproducidos de la auditoría sin corregir dentro del motor. La aprobación recibida se limita al subconjunto y restricciones descritos, mantiene OT-FORMAT sin recuperación y deja documentada la limitación residual de regeneración binaria entre sistemas. No se afirma reproducibilidad integral en un entorno que no se ha ejecutado.

## 11. Preparación para la Fase 1B

La futura Fase 1B puede consumir capas, transformaciones, estados y dependencias completos. Deberá distinguir recuperación textual, evidencia contextual, operaciones añadidas por el lanzador y comportamiento funcional; no debe asignar una etiqueta por una cadena aislada ni convertir referencias manuales en evidencia del modelo. Mantendrá DEV-01, DEV-02 y DEC-01.

La Fase 1A queda cerrada con la autorización recibida. Antes de iniciar la Fase 1B, el responsable revisará y publicará los cambios y deberá autorizar su inicio por separado. La limitación residual de serialización del piloto permanece documentada para cualquier comprobación binaria de derivados fuera del entorno actual; no impide consumir el motor estático, pero no debe darse por resuelta en la evaluación experimental.

Para la revisión y publicación del cambio completo de la Fase 1A: este registro, [deobfuscator.md](deobfuscator.md), los ocho módulos de `backend/app/services/deobfuscation/`, el esquema, las cuatro suites y las fixtures de `backend/tests/deobfuscation/`, `backend/tests/test_repository_line_endings.py`, la demo, `.gitattributes`, `README.md`, [architecture.md](architecture.md) y [roadmap.md](roadmap.md). Son 25 archivos pendientes de publicación: cuatro modificados ya versionados y 21 nuevos. El commit y el push corresponden al responsable.
