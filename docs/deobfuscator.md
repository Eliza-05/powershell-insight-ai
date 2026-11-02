# Motor de desofuscación estática — Fase 1A

**Estado:** Fase 1A aprobada técnicamente y cerrada por autorización expresa del responsable dentro del subconjunto descrito aquí; [acta, pruebas y reproducibilidad](phase1a_closure.md). La publicación corresponde al responsable. La Fase 1B permanece sin autorizar ni iniciar; no se implementan sus reglas, la aplicación web ni la evaluación A/B/C. La autorización para esta fase es posterior al [cierre de la Fase 0B](phase0b_closure.md), cuyo registro se conserva.

## 1. Objetivo y alcance

El servicio recibe texto PowerShell no confiable y recupera valores mediante operaciones de Python sobre cadenas y bytes. No ejecuta el texto, no invoca PowerShell ni .NET, no abre sus rutas, no consulta sus destinos y no llama a Ollama. No produce etiquetas B01–B07 ni riesgos. Una recuperación textual no demuestra que el código sea alcanzable, que vaya a ejecutarse ni que sea malicioso.

La implementación es un **reconocedor limitado con lexer y gramática de expresiones**, no el parser oficial de PowerShell. Conserva el original y extrae artefactos; no genera un script reescrito ni afirma equivalencia semántica completa. `semantic_equivalence` siempre vale `not_claimed`. Las técnicas detectadas describen patrones sintácticos compatibles, no prueban intención de ofuscar.

## 2. Arquitectura implementada

| Componente | Responsabilidad |
|---|---|
| `backend/app/schemas/deobfuscation.py` | Contratos Pydantic específicos, límites, estados y validación de referencias, rangos y dependencias |
| `services/deobfuscation/lexer.py` | Separa comentarios, literales, variables, delimitadores y operadores con offsets; mantiene contenido opaco fuera del subconjunto |
| `expressions.py` | Construye expresiones de literales, paréntesis, concatenación y llamadas textuales permitidas antes de recuperar valores |
| `transforms.py` | Base64 estricto, conversiones explícitas de codificación y concatenación acotada |
| `encoded_command.py` | Reconoce argumentos de un lanzador literal en posición de comando |
| `variables.py` | Identifica variables elegibles y excluye ámbitos, reasignaciones y valores automáticos |
| `budget.py` | Presupuesto determinista de trabajo y espacio, con errores de límite controlados |
| `engine.py` | Coordina expresiones, definiciones/usos, registros de transformación y recorrido de capas decodificadas |
| `__init__.py` | Expone `deobfuscate` como API pública |
| `experiments/demo_deobfuscation.py` | Demostración Python con texto propio e inerte, sin escribir resultados ni usar servicios |

Se reutiliza `ObfuscationTechnique` del contrato existente sin modificarlo. El resto del contrato del LLM permanece separado. No se añadieron dependencias; se usan Python estándar y el Pydantic ya instalado.

## 3. Subconjuntos reconocidos

### OT-B64-ENCCMD

- Nombres literales `powershell`, `powershell.exe`, `pwsh` y `pwsh.exe`, sin distinción de mayúsculas, al comienzo de una sentencia. También `& 'pwsh.exe'` o un nombre literal equivalente; no se resuelven rutas ni variables como ejecutables.
- Solo `-EncodedCommand` y `-enc`, sin distinción de mayúsculas. Antes de ellos se admiten los indicadores completos `-NoProfile`, `-NoLogo` y `-NonInteractive`.
- Un único argumento final, literal sin comillas o una cadena entre comillas del subconjunto. No admite argumentos dinámicos, concatenaciones del argumento, parámetros posteriores, `-e`, `-ec`, `/enc` ni formas con `:`. No busca parámetros dentro de `-Command` o `-File`.
- Los argumentos exigen separación explícita por espacio, tabulador o salto de línea no escapado. Una continuación con acento grave elimina ese salto y por sí sola no separa argumentos. Las comillas pegadas a `-enc` quedan fuera del subconjunto. La separación solo mediante un comentario de bloque también se excluye conservadoramente.
- Base64 estándar, padding válido, bytes interpretados estrictamente como UTF-16LE. No repara entradas truncadas, prueba otras codificaciones ni usa heurísticas de alfabetos alternativos.
- Registra `added_operation = LAUNCHER_ENCCMD`, sin atribuir B02. Es una forma sintáctica de lanzador: no verifica qué ejecutable, alias o función resolvería el sistema.
- El texto obtenido genera una capa hija, conservada íntegra, que vuelve a pasar por el reconocedor. El argumento Base64 y el texto decodificado tienen posiciones distintas y explícitas.

La decodificación correcta demuestra una conversión de bytes a texto, **no** validez sintáctica completa de PowerShell. Si bytes de otra codificación también forman UTF-16LE válido, no siempre puede detectarse su origen real. El lexer de la capa hija informa la sintaxis que no puede interpretar.

### OT-B64-INLINE

Reconoce expresiones de estas formas, sin distinción de mayúsculas en nombres de tipos y miembros:

```powershell
[Convert]::FromBase64String('bGFiLW9ubHk=')
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('bGFi' + 'LW9ubHk='))
```

Los tipos permitidos son `Convert`/`System.Convert` y `Text.Encoding`/`System.Text.Encoding`; la lista de codificaciones es **Unicode (UTF-16LE), BigEndianUnicode (UTF-16BE), UTF8 y ASCII**. Se admiten paréntesis, concatenaciones de literales y variables con un valor permitido. No se llaman los métodos .NET: se reconoce su forma y se calcula la operación equivalente del subconjunto con Python.

Sin codificación explícita se preservan **bytes como Base64**, con estado `partial` y advertencia; no se inventa texto. Con codificación desconocida o texto incompatible se mantienen los bytes recuperados y se registra el fallo de conversión. Se rechazan BOM contradictorio, secuencias Unicode inválidas, caracteres de control binario y caracteres no asignados (se permiten tabulador, CR y LF). La política es más restrictiva que conversiones que reemplazan bytes inválidos.

El texto inline recuperado **no** se vuelve a interpretar como código: puede ser un mensaje o un dato. Únicamente `EncodedCommand` abre capas de script. No se reconocen cadenas que solo parecen Base64, compresión, XOR, cifrado, `Encoding.Default`, `GetEncoding`, casts o llamadas arbitrarias.

### OT-CONCAT

Gramática: literales entre comillas, variables permitidas y subexpresiones entre paréntesis, unidos por `+`. La concatenación exige operandos de tipo cadena; no realiza conversiones implícitas, sumas numéricas ni concatenación de arrays. Soporta varios operandos, cadenas vacías, Unicode y anidamiento limitado.

- Comillas simples: texto literal, con `''` como apóstrofo. El acento grave y `$` permanecen literales.
- Comillas dobles: sin interpolación; permite comillas duplicadas y los escapes de acento grave `0`, `a`, `b`, `e`, `f`, `n`, `r`, `t`, `v`, acento grave, comillas y dólar. También reconoce continuación de línea explícita.
- Una cadena expandible con `$` no se resuelve; subexpresiones `$()` en comillas dobles ponen la capa fuera del subconjunto. Los escapes no incluidos, here-strings, comillas tipográficas e identificadores escapados no se reinterpretan.
- Respeta la separación entre modo expresión y argumentos. `'a' + 'b'` como expresión produce `ab`; `Write-Output 'a' + 'b'` no produce esa concatenación. Sí se recupera el valor de `Write-Output ('a' + 'b')` como subexpresión, sin afirmar nada sobre el comando.
- Comentarios de línea y bloque (incluidos anidados) y cadenas que contienen código aparente no se transforman. Una anomalía léxica fatal o delimitadores desbalanceados impiden recuperar toda esa capa; no se rescata texto de sintaxis rota como si fuera válido.
- Un `#` unido a un argumento sin comillas se conserva como parte del argumento; no se recorta una cola Base64 inválida como si fuera un comentario. Se reconocen comentarios de línea con separación o frontera de sentencia; formas adyacentes ambiguas quedan fuera del subconjunto. `--%` vuelve opaca la capa completa para no interpretar sus argumentos literales.

### OT-VARSUB

Resolución simbólica **local a una capa**, con nombres ASCII simples y comparación sin distinción de mayúsculas. Solo asignaciones únicas `$nombre = expresión` con resultado cadena, anteriores al uso. Cada definición y cada uso tienen transformación propia, con dependencias hacia su origen. Se admiten dependencias entre variables conocidas y concatenaciones, dentro del presupuesto.

Política conservadora:

- Cualquier reasignación, asignación compuesta o incremento/decremento detectado invalida esa variable en toda la capa, incluso antes de la segunda escritura.
- Una escritura mediante un nombre no admitido, incluidas las formas con llaves o ámbito explícito, deshabilita las sustituciones de toda la capa: podría modificar el mismo nombre simple. Se incluyen `%=` y `??=` en la exclusión de asignaciones compuestas, sin calcular esos operadores.
- Llaves de bloques, funciones, condicionales, bucles, declaraciones y contextos de ámbito no soportados deshabilitan las sustituciones de la capa. No se hace análisis de flujo ni de alcanzabilidad.
- El tramo de valores conocidos termina en el primer comando con posibles efectos o una asignación cuyo resultado no sea puro y recuperable. No se propagan valores a través de esos efectos. Los argumentos simples de ese primer comando pueden usar valores previos; argumentos dinámicos o con paréntesis deshabilitan esa sustitución de argumentos.
- Variables de entorno, ámbitos explícitos, variables con llaves, nombres automáticos reservados y preferencias no se consultan ni se sustituyen. Tampoco se resuelven propiedades, índices, resultados de comandos, funciones, referencias o llamadas dinámicas.
- No sustituye dentro de comentarios ni de cadenas. Un nombre desconocido queda localizado como no resuelto. Las asignaciones no se ejecutan y los usos recuperados no prueban que el comando llegue a ejecutarse.

Esto sacrifica cobertura para evitar atribuir valores después de posibles efectos. En P3, `Join-Path` es una barrera: las cadenas del cmdlet y de la URL se recuperan por sus concatenaciones, sin inventar el resultado de la variable de destino.

### OT-FORMAT y sintaxis fuera del alcance

El operador `-f` se reconoce en posiciones de expresión, también dentro de paréntesis, con transformación `unsupported` y fragmento no resuelto. **No se formatea la cadena.** Un `-f` usado como parámetro de comando o dentro de una cadena/comentario no se atribuye a esta técnica. P7 conserva esta limitación.

No se implementan el lenguaje completo, scripts reescritos, interpretación de arrays/hashtables, interpolación, tipos y métodos arbitrarios, `OT-IO-*`, compresión, reflexión, análisis de módulos, ni recuperación de contenido externo.

Una subexpresión entre paréntesis usada como argumento que el parser no admite genera un fragmento no resuelto y estado global `partial`. Puede conservarse una concatenación interior admitida con su propio rango, sin presentar la expresión exterior como recuperada. Se reconocen líneas LF y CRLF; no se garantiza segmentación de scripts con separadores exclusivamente CR.

## 4. API Python y contratos

Desde `backend/`, usando el intérprete del entorno existente:

```python
from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation import deobfuscate

script = "$message = 'training-' + 'only'\nWrite-Output $message\n"
result = deobfuscate(
    script,
    source_name="inert-example",
    input_provenance="original",
    limits=DeobfuscationLimits(max_depth=3),
)
print(result.model_dump_json(indent=2))
print(result.recovered_texts())
```

`source_name` es una etiqueta lógica: el servicio no lee ese archivo. `input_provenance` admite `original`, `obfuscated_variant` (predeterminado), `reference_manual` y `reference_decoded`. No acepta `model_recovered`. La procedencia no se deduce del contenido: la declara quien llama.

| Campo del resultado | Significado |
|---|---|
| `schema_version`, `engine_version` | `deobfuscation-v1`, `static-subset-v1` |
| `input_sha256`, `input_provenance`, `source_name` | Identidad del texto y procedencia declarada; SHA-256 sobre UTF-8 sin normalizar |
| `layers` | Original `L0` y capas decodificadas `L1`, etc., con texto, profundidad y transformación padre |
| `transformations` | Registros `T0001`, etc., en orden determinista, con técnica, fragmento exacto, rango, contenido recuperado, clase, dependencias, estado y advertencias |
| `unresolved` | Rangos y motivos de ambigüedad, sintaxis no soportada o fallo; no se pierden silenciosamente |
| `techniques_detected` | Vocabulario `ObfuscationTechnique`, ordenado y sin duplicados |
| `limits`, `limits_hit`, `work_units`, `artifact_bytes` | Configuración efectiva, motivos de parada y contadores; no son medidas de latencia |
| `status`, `warnings` | `complete`: terminó el reconocimiento sin incidencias detectadas; `partial`: hubo limitaciones; `rejected`: entrada fuera del contrato de texto/tamaño |

`complete` **no** significa desofuscación completa del lenguaje. Los IDs son estables para la misma entrada y configuración, no identificadores permanentes entre ediciones del script. No hay timestamps ni dependencia de estado global en el resultado.

Los modelos usan `extra="forbid"`. La validación comprueba el hash de L0, rangos y líneas, fragmentos literales, referencias a capas, vínculos padre/hijo y dependencias anteriores (sin ciclos). Errores de uso de la API —tipo de entrada, metadatos o configuración inválidos— producen `TypeError`/`ValidationError`. Sintaxis no confiable, Base64 inválido y límites producen resultados estructurados. Una entrada rechazada por tamaño no se copia en `layers` ni se calcula su hash (`input_sha256 = null`).

## 5. Trazabilidad y procedencia

Los offsets son índices de **puntos de código Unicode de Python**, empezando en 0 y con extremo final exclusivo. Líneas y columnas empiezan en 1; un tabulador cuenta como un carácter. No son offsets UTF-8 ni unidades UTF-16. El texto original conserva CRLF y Unicode exactamente como se recibió.

Ejemplo de transformación para la entrada `'sun' + 'rise'` (extracto del resultado):

```json
{
  "transformation_id": "T0001",
  "technique": "OT-CONCAT",
  "source": {"layer_id": "L0", "start": 0, "end": 14, "line": 1, "column": 1, "end_line": 1, "end_column": 15},
  "root_source": {"layer_id": "L0", "start": 0, "end": 14, "line": 1, "column": 1, "end_line": 1, "end_column": 15},
  "original_fragment": "'sun' + 'rise'",
  "provenance": "deobfuscator_recovered",
  "recovery_kind": "string",
  "recovered_text": "sunrise",
  "recovered_bytes_base64": null,
  "dependencies": [],
  "status": "success",
  "deterministic_verified": true,
  "warnings": [],
  "added_operation": null,
  "output_layer_id": null
}
```

En una concatenación dentro de un `EncodedCommand`, `source` señala **L1**, donde existe la expresión. `root_source` señala el argumento Base64 de **L0**, como ancla de derivación, no como ubicación literal de la expresión decodificada. `dependencies` incluye la transformación que creó L1. Una sustitución añade la transformación de definición de la variable. El contrato impide atribuir a L0 un fragmento que solo existe en una capa hija.

`deterministic_verified` certifica únicamente la transformación del subconjunto. Los bytes sin interpretación son verificables pero `partial`; los estados `failed`/`unsupported` no llevan contenido recuperado ni verificación positiva. La procedencia de todos los artefactos del motor es `deobfuscator_recovered`, incluso cuando la entrada declarada era una referencia del equipo; el origen de la capa raíz se mantiene separado.

El contrato exige bytes Base64 válidos, tipo `bytes` y verificación positiva para una transformación `partial`; un resultado `complete` no puede contener fragmentos no resueltos ni límites alcanzados. Los modelos congelados impiden reasignar campos, pero sus listas no son profundamente inmutables. Un consumidor que altere un payload debe volver a validarlo con `DeobfuscationResult.model_validate` antes de confiar en su traza.

`result.recovered_texts()` ofrece un mapa con claves `deobfuscator_recovered:T…` para `literal_check.locate(snippet, script, references=...)`. Una coincidencia `REFERENCE_EXACT` prueba existencia literal, no respaldo semántico ni recuperación del modelo. El adaptador conserva IDs; el consumidor debe guardar también el resultado completo. No se cambia la política de evidencia del piloto ni se equipara la referencia del equipo con salida del motor/LLM.

## 6. Límites y seguridad

| Límite | Predeterminado | Máximo configurable |
|---|---:|---:|
| Entrada UTF-8 (`max_input_bytes`) | 1 MiB | 4 MiB |
| Valor recuperado (`max_artifact_bytes`) | 256 KiB | 1 MiB |
| Contenido acumulado (`max_total_artifact_bytes`) | 2 MiB | 8 MiB |
| Transformaciones | 512 | 4096 |
| Capas decodificadas desde L0 (`max_depth`) | 3 | 8 |
| Anidamiento de expresión/delimitadores | 24 | 48 |
| Términos expandidos de concatenación | 128 | 1024 |
| Tokens por capa | 50 000 | 200 000 |
| Unidades de trabajo acumuladas | 4 000 000 | 16 000 000 |
| Fragmentos no resueltos | 128 | 1024 |

El acumulado contabiliza contenido recuperado, copias de los fragmentos de origen y capas hijas serializadas; no incluye L0, limitado por separado, ni todo el overhead de objetos Python/JSON. El tamaño de valor mide bytes decodificados o UTF-8; la representación Base64 de bytes cuenta en el acumulado. Se comprueba el tamaño esperado antes de decodificar y antes de unir cadenas. Los términos se propagan por variables, de modo que duplicar valores sucesivamente no elude el límite.

Al alcanzar un límite se detiene el trabajo restante y se devuelven los artefactos anteriores, `partial`, `limits_hit` y una advertencia. No se itera sobre scripts reescritos: se recorren solo capas nuevas, con profundidad acotada. La misma entrada/configuración genera el mismo orden, IDs y resultado.

**Presupuesto de tiempo:** se limita el trabajo de forma determinista (caracteres/tokens visitados, operaciones del parser y volumen transformado), además de memoria y profundidad. No se usa un plazo de reloj que haría depender el resultado de la carga del equipo. No es una garantía de latencia en segundos ni un sandbox de proceso; un futuro servicio puede añadir aislamiento/timeout externo, sin ejecutar las muestras. El motor tampoco lee `.env`; los límites se pasan explícitamente y el valor por defecto de entrada coincide con el 1 MiB documentado.

Las pruebas revisan el AST del servicio para impedir imports de ejecución/red/archivos y llamadas dinámicas, además de la prueba estática anterior que recorre `backend/app` y `experiments`. También se interceptan creación de procesos y sockets durante una recuperación de contenido adversario inerte. Esto complementa la revisión del código; no pretende demostrar formalmente la seguridad de Python o sus dependencias.

## 7. Decisiones respecto a la propuesta

| Decisión | Resolución y motivo |
|---|---|
| Prefijos de `EncodedCommand` | Solo nombre completo y `-enc` en un lanzador reconocible; las formas cortas adicionales se dejan fuera para evitar ambigüedad |
| Variables y reasignaciones | Asignación única por capa, sin ramas, y barrera tras efectos. Las reasignaciones lineales también se excluyen; se prioriza procedencia verificable |
| Piloto como fixtures | P2/P3/P4/P6/P7 solo son regresiones; no cambian de split ni pasan a un dataset de evaluación. Se añaden fixtures propias y variantes sintéticas separadas |
| Recuperación de referencia | `reference_recovery.py` permanece congelado e independiente; solo se importa en pruebas de igualdad |
| Composición | Solo las decodificaciones `EncodedCommand` abren capas. Los valores inline permanecen datos, sin asumir que son código |
| Tiempo frente a determinismo | Presupuesto de trabajo en vez de parada por reloj; límites duros configurables para evitar expansión y recursión sin cota |
| Organización | Un módulo de transformaciones puras y uno de variables, en lugar de un archivo por cada operación pequeña; lexer, parser, contratos y orquestación siguen separados |
| Semántica | No se normaliza ni reescribe el script; artefactos y relaciones explícitas, sin equivalencia completa ni etiquetas de comportamiento |

DEV-01 sigue vigente: no se selecciona ni se ajusta el LLM y no hay llamadas a Ollama. La solicitud de implementar la Fase 1A autoriza este incremento; no autoriza la Fase 1B.

## 8. Pruebas, demostración y regresiones

Desde la raíz, con el entorno existente:

```powershell
.\.venv\Scripts\python.exe -B experiments\demo_deobfuscation.py
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend\tests
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend\tests\deobfuscation
```

Estos comandos ejecutan **Python**, nunca el texto PowerShell analizado. Si el directorio temporal predeterminado de pytest no tiene permisos, usar `--basetemp` con una ruta nueva cuyo directorio padre exista. La auditoría utilizó un directorio único bajo `%TEMP%`, fuera del repositorio, sin eliminar archivos; `-B` evita bytecode y `-p no:cacheprovider` evita la caché de pytest.

| Pruebas | Alcance |
|---|---|
| `test_engine.py` | Contratos básicos, técnicas, entradas inválidas, límites y regresiones del piloto |
| `test_variants.py` | Variantes sintéticas adicionales, negativos de contexto, reasignaciones, expansiones, Unicode y 180 entradas malformadas de semilla fija |
| `test_contract_security.py` | Integridad de trazas, ausencia de rutas de ejecución/red, procedencias, contratos JSON, fixtures y demo |
| `test_audit_regressions.py` | 30 casos de auditoría: alias, asignaciones compuestas, argumentos nativos, diagnósticos, corrupción de contratos, trazas Unicode anidadas, ausencia de I/O y demo desde otro directorio |
| `backend/tests/test_repository_line_endings.py` | Tres regresiones de cierre: filtros Git con core.autocrlf=false/true/input reproducen 18 hashes históricos; no crean un checkout nuevo |
| `fixtures/*.ps1.txt`, `fixtures/manifest.json` | Dos fixtures propias e inertes, con SHA-256, tamaño y cadenas esperadas. LF fijado en `.gitattributes`; no son datos de investigación |

Las pruebas adicionales están separadas de las de desarrollo/piloto, pero **no son un conjunto de prueba ciego** ni aportan una estimación de generalización. Sus oráculos son valores literales o conversiones explícitas, nunca respuestas del LLM.

| Caso | Resultado exigido y comprobado |
|---|---|
| P2 | Capa UTF-16LE idéntica a `reference/PILOT-P2_decoded.ps1.txt` y a la recuperación de referencia; `Get-Process` visible |
| P3 | `Invoke-WebRequest` y `https://example.com/report.csv` recuperados; limitación explícita para `Join-Path` y propagación posterior |
| P4 | Literales de las variables (`…CurrentVersion\Run`, `PilotLabUpdater`, ruta inerte) con definición y usos localizados |
| P6 | Capa idéntica a su referencia; `IEX` y `DownloadString` visibles sin etiquetas funcionales; `Net.WebClient` y URL recuperados por concatenación. Estado global `partial` por la expresión exterior `New-Object`, fuera del subconjunto |
| P7 | Tres expresiones `-f` detectadas como no soportadas; no se inventa su resultado |

## 9. Criterios de terminación técnica y continuidad

La aceptación técnica requiere las cuatro técnicas dentro de estos subconjuntos, `OT-FORMAT` explícitamente no soportada, regresiones correctas, original preservado, trazabilidad validada, límites efectivos, pruebas anteriores/nuevas aprobadas, demo Python, documentación coincidente e integridad del piloto. El responsable ha aprobado ese alcance y autorizado el cierre de la Fase 1A; las operaciones Git y una futura autorización de la Fase 1B siguen siendo suyas.

**Auditoría aprobada:** 271 pruebas: 82 anteriores, 159 de implementación y 30 de auditoría. **Validación final de cierre:** 274 pruebas aprobadas, 0 fallidas y 0 omitidas, incluyendo tres regresiones de finales de línea; **5,36 s** observados, sin garantía de latencia. La demo pasó también desde otro directorio de trabajo. Los históricos conservan sus bytes y hashes. Excepciones acotadas en `.gitattributes` permiten reconstruir los hashes registrados de 18 archivos mediante filtros Git bajo tres valores de core.autocrlf, sin crear un checkout nuevo. El [acta](phase1a_closure.md) distingue ese ajuste de la limitación residual: regenerar derivados del piloto en otro sistema puede producir iguales datos y métricas con bytes diferentes; el evaluador sigue intacto. No hay temporales de pruebas dentro del repositorio y no se eliminaron archivos.

La Fase 1B debe consumir **capas y transformaciones completas**, no solo cadenas sueltas. Primero debe definir el contrato de hallazgos deterministas, la política de evidencia contextual y la separación entre operaciones añadidas y comportamientos B01–B07. Después podrá implementar reglas por categoría con fixtures propias, familias separadas y pruebas negativas. No se implementó ninguna regla, clasificador de riesgo, generador de variantes ni pipeline A/B/C en esta fase.

## 10. Fuentes de semántica consultadas

El subconjunto de comillas y escapes se contrastó con [about_Quoting_Rules](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules?view=powershell-7.5). La distinción entre expresiones y argumentos sigue [about_Parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing?view=powershell-7.5). La conversión UTF-16LE del argumento y la sensibilidad a mayúsculas se contrastaron con [about_PowerShell_exe](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_powershell_exe?view=powershell-5.1). Son referencias de sintaxis; el reconocedor no implementa todas sus formas.

La auditoría contrastó las escrituras con nombres alternativos con [about_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_variables) y [about_Scopes](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_scopes), y los operadores excluidos con [about_Assignment_Operators](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_assignment_operators). No se ejecutaron ejemplos de esas páginas.
