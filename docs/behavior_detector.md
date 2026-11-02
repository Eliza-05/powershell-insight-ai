# Motor determinista de comportamientos — Fase 1B

**Estado:** aprobado técnicamente y cerrado formalmente por autorización expresa del responsable dentro del subconjunto descrito, con las limitaciones y falsos negativos P3/P7 aceptados; [acta de cierre](phase1b_closure.md). Publicación pendiente a cargo del propietario. La Fase 2 permanece bloqueada por la selección definitiva del LLM; no se inicia ni se ejecuta el experimento A/B/C. La autorización de implementación fue posterior a la publicación de la Fase 1A en `562f91cb13a1a778b62ec5ba1e8b5ae683f8c201`.

## 1. Alcance y decisiones

La API Python `analyze_behaviors` recibe texto no confiable, ejecuta el desofuscador estático existente y reconoce invocaciones y relaciones de argumentos en L0 y las capas de script derivadas. Produce etiquetas B01–B07, hallazgos con evidencia verificable e indicios separados cuando falta soporte. No determina malware, intención, riesgo ni probabilidad de confianza. No ejecuta el texto.

Se conserva la [taxonomía v0.2](behavior_taxonomy.md), la política estricta de [methodology.md](methodology.md) y DEV-01/DEV-02/DEC-01. No se modifican las muestras, anotaciones, reglas de evaluación, métricas, resultados ni contratos de las fases anteriores. Qwen2.5-Coder 7B sigue siendo candidato provisional; no se consulta al modelo.

Hay doce reglas que cubren un subconjunto de las siete categorías. `coverage_partial` siempre es `true`: no existe cobertura completa del lenguaje. `complete` significa que finalizó el reconocimiento sin incidencias detectadas, no que el script se haya entendido íntegramente. Un hallazgo está respaldado estáticamente dentro del subconjunto, sin demostrar ejecución efectiva o alcanzabilidad general.

## 2. Arquitectura

| Archivo | Responsabilidad |
|---|---|
| `backend/app/schemas/behavior_detection.py` | Contratos versionados, límites, procedencia y validación de integridad referencial |
| `backend/app/services/behavior_detection/__init__.py` | API pública |
| `extraction.py` | Reconocedor acotado de invocaciones, grupos de argumentos y receptor WebClient inmediato |
| `rules.py` | Catálogo estable y condiciones positivas/negativas/contextuales puras |
| `engine.py` | Integración 1A, presupuestos, construcción transaccional de evidencias/hallazgos y deduplicación |
| `backend/tests/behavior_detection/` | Ejemplos inertes propios, pruebas de reglas, integración, contratos y seguridad |
| `experiments/demo_behavior_detection.py` | Demo Python portable con JSON por stdout |

No se añadió un lexer ni un parser general. Se reutilizan `deobfuscation.lexer.lex`, `validate_delimiters`, `Budget`, `LimitReached` y el separador `_statements` de 1A. Este último es un helper interno: se documenta el acoplamiento y las regresiones verifican su integración. Ningún archivo de implementación de 1A se modificó. La extracción nueva solo reconoce posiciones de comando y argumentos del subconjunto; no calcula otra vez concatenaciones ni variables.

Los valores de expresiones se toman exclusivamente de transformaciones locales `success`, verificadas, de tipo cadena/uso de variable. El extractor puede quitar paréntesis que envuelvan un operando completo y consultar su rango interior. Un nombre de comando reconstruido se acepta en una invocación explícita con `&`, únicamente si 1A verificó ese uso concreto. No se enlazan valores por su nombre o porque aparezcan cerca.

Un bareword se considera literal únicamente en modo argumento: `(Get-UnresolvedTarget)` es un comando cuyo resultado se desconoce, no la cadena Get-UnresolvedTarget. Los paréntesis solo conservan valores de literales, booleanos explícitos o recuperaciones verificadas. El constructor WebClient exige separadores reales después de New-Object y de -TypeName; una continuación escapada por sí sola no separa argumentos.

## 3. Catálogo B01–B07

Los IDs están fijados por `static-behaviors-v1`. Cada `RuleSpec` contiene categoría, descripción, condición positiva, negativos, evidencia mínima y limitación. Las condiciones efectivamente utilizadas se guardan también en cada hallazgo.

| Regla | Condiciones y evidencia necesarias | Negativos y límites principales |
|---|---|---|
| BD-B01-WEBGET | Invoke-WebRequest/Invoke-RestMethod, URI HTTP(S) literal o recuperada, GET explícito o predeterminado. Cita invocación, URI y método cuando existe | URL aislada, HEAD, método desconocido, duplicados, argumentos no admitidos o URI dinámica no confirman B01. Sin alias curl/wget, FTP, SMB o BITS |
| BD-B01-WEBCLIENT | Receptor inmediato `(New-Object [System.]Net.WebClient)`, DownloadString con una URI HTTP(S), o DownloadFile con URI y destino estáticos. Cita receptor, operación y argumentos | No objetos guardados en variables, métodos arbitrarios, DownloadData, receptores desconocidos ni destino omitido |
| BD-B02-IEX | IEX/Invoke-Expression en posición de comando con cadena estática no vacía, o un DownloadString remoto inmediato como entrada; también `-Command`. Cita evaluador y entrada relacionada | No términos en texto, EncodedCommand, `&` por sí solo, entrada desconocida o pipeline sin relación probada. No interpreta el texto literal recibido para extraer otros comportamientos |
| BD-B03-RUNWRITE | New-ItemProperty/Set-ItemProperty con `-Path` exacto HKCU/HKLM Software/Microsoft/Windows/CurrentVersion/Run o RunOnce, `-Name` y `-Value` no vacíos. Si hay PropertyType, String/ExpandString | Lecturas, RunArchive, valores desconocidos/vacíos o tipos no textuales. No tareas programadas, servicios, WMI, perfiles o carpetas Startup |
| BD-B04-DEFENDER-DISABLE | Set-MpPreference con DisableRealtimeMonitoring y booleano literal `$true`; cita operación y booleano | `$false` restaura la protección y no genera B04; cadenas o variables sin valor booleano literal no bastan. No afirma éxito |
| BD-B04-DEFENDER-EXCLUSION | Add-MpPreference con ExclusionPath estático no vacío; cita operación y exclusión | Consultar, eliminar una exclusión o usar valor desconocido no confirma B04 |
| BD-B04-FIREWALL-DISABLE | Set-NetFirewallProfile con Enabled booleano literal `$false`; Profile opcional conocido Domain/Private/Public. Cita operación, booleano y perfil si existe | `$true` no genera B04. Perfil desconocido/vacío/inválido genera abstención. No arrays, reglas individuales ni resolución de perfiles en ejecución |
| BD-B05-HOSTQUERY | Get-Process, Get-Service, Get-ComputerInfo, Get-NetIPConfiguration, Get-MpComputerStatus o Get-MpPreference en posición de comando | Texto/comentarios y palabras en argumentos no son consultas. No clasifica estas consultas como maliciosas |
| BD-B05-RUNQUERY | Get-ItemProperty con Path Run/RunOnce estático; cita consulta y ruta | No es B03: no hay escritura. No se generaliza a cualquier lectura del registro |
| BD-B06-HTTP-SEND | Invoke-WebRequest/Invoke-RestMethod con URI HTTP(S), POST/PUT/PATCH y Body estático no vacío; cita operación, URI, método y cuerpo | GET no genera B06. No basta el método si falta el cuerpo. No afirma exfiltración, C2 ni una descarga por la respuesta HTTP |
| BD-B06-CONNECTIVITY | Test-NetConnection con ComputerName literal/recuperado o primer argumento posicional | Destino desconocido o dirección aislada no bastan. Sin sockets, sesiones remotas, canal DNS o API cloud |
| BD-B07-STORED-CREDENTIAL | Get-StoredCredential con Target literal/recuperado o primer argumento posicional; cita acceso al almacén y target | Get-Credential, palabras password/token o target desconocido no bastan. No lectura de LSASS, SAM, navegador ni búsqueda general de secretos |

Los nombres no distinguen mayúsculas. Se usan parámetros completos; no se resuelven abreviaturas o alias no especificados. Se permiten solo las formas de argumentos documentadas por cada regla; duplicados y condiciones incompletas producen indicios. Los booleanos defensivos requieren `$true`/`$false`, sin conversiones implícitas de cadenas o enteros.

Las reglas HTTP comprueban esquema/hostname y sintaxis/rango del puerto explícito; esto no prueba que el servidor exista ni es validación integral de todos los formatos URI. Las claves Run/RunOnce requieren `HKCU:\`/`HKLM:\` o `Registry::HKEY_CURRENT_USER\`/`Registry::HKEY_LOCAL_MACHINE\`: una ruta relativa que solo empieza por HKCU no prueba acceso al registro. Las restauraciones con booleanos reconocidos no generan B04 ni un indicio erróneo de comando fuera del catálogo; el resultado global aún puede ser partial por las limitaciones de 1A.

Las operaciones HTTP siguen la distinción de método y cuerpo de [Invoke-WebRequest](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/invoke-webrequest). La desactivación y restauración se contrastaron con la [documentación de protección en tiempo real de Defender](https://learn.microsoft.com/en-us/defender-endpoint/configure-real-time-protection-microsoft-defender-antivirus); el cambio de perfiles con la [documentación de Windows Firewall](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/configure-with-command-line). Get-StoredCredential se reconoce como acceso al almacén según el [código fuente del módulo CredentialManager](https://github.com/davotronic5000/PowerShell_Credential_Manager/blob/master/PSCredentialManager.Cmdlet/Cmdlets.cs). Se consultó documentación y código como texto: no se instalaron ni ejecutaron esos módulos.

Los ajustes de auditoría se contrastaron con [about_Parsing](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_parsing) y [about_Registry_Provider](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_registry_provider). No se ejecutaron sus ejemplos.

## 4. Procedencia funcional y wrappers

EncodedCommand solo abre una capa a través de 1A y conserva `LAUNCHER_ENCCMD`; no genera B02. El operador `&` que invoca un comando conocido/reconstruido tampoco genera B02 automáticamente.

Para IEX se distingue la operación de evaluación y su procedencia. La entrada predeterminada se declara `original`. Si el llamador declara `obfuscated_variant`, un IEX en L0 queda como indicio porque podría ser un wrapper añadido. Las capas decodificadas por un lanzador conocido pueden aportar el IEX que contienen: se excluye el lanzador, no la lógica interior. Si hay otros wrappers añadidos, el llamador debe declararlos mediante `AddedOperation(operation='EXEC_WRAPPER_IEX', source=...)`, indicando el rango exacto del nombre de comando IEX en su capa. Ese IEX se excluye de B02; su descarga interior puede seguir aportando B01.

No se puede deducir de la sintaxis si un IEX no declarado dentro de una recuperación fue añadido por otra transformación. La procedencia de entrada y el historial de wrappers son metadatos del llamador, no hechos inferidos ni etiquetas esperadas. Un historial falso/incompleto puede producir una interpretación funcional incorrecta; se comunica como limitación. Se valida que los wrappers declarados apunten a invocaciones reconocidas, sin duplicados y dentro de las cotas.

El servicio no acepta referencias manuales, decodificadas por el equipo o del modelo como procedencia de entrada, ni un resultado de desofuscación proporcionado externamente. Siempre llama a 1A sobre el texto recibido. No abre el manifiesto, las anotaciones o las respuestas del piloto. `source_name` es solo una etiqueta lógica y nunca una ruta que se lea.

## 5. API Python y contrato JSON

```python
from app.services.behavior_detection import analyze_behaviors

script = "$op='Invoke-'+'WebRequest'; $uri='https://'+'example.com/cedar'; & $op -Uri $uri"
result = analyze_behaviors(script, input_provenance="original", source_name="own-inert-example")
print(result.behaviors)
print(result.model_dump_json(indent=2))
```

La salida incluye B01, un único hallazgo contextual, la operación y los valores recuperados con sus IDs de transformación. No incluye riesgo ni probabilidades.

| Contrato | Campos principales |
|---|---|
| BehaviorAnalysisResult | Versiones, status, coverage_partial, deobfuscation completo, detection_limits, added_operations, behaviors, findings, evidence, indicators, obstructing_techniques, warnings, limits_hit y contadores |
| BehaviorFinding | finding_id, behavior_id, rule_id, description, operation_source, evidence_ids, support, conditions, limitations |
| DetectionEvidence | evidence_id, role, source, root_source, fragment literal, provenance, recovered_value opcional, transformation_ids |
| BehaviorIndicator | indicator_id, behavior_id/rule_id opcionales, source y motivo de abstención |

`behaviors` se deriva solo de hallazgos respaldados; los indicios no añaden etiquetas. `support='individual'` significa que la regla cita una evidencia de operación; `contextual` significa que cita varias piezas relacionadas. Es el conjunto de citas del detector, no un nuevo veredicto sobre las anotaciones históricas. Pueden existir etiquetas respaldadas en un resultado global `partial`.

El modelo Pydantic prohíbe campos adicionales y valida IDs únicos, catálogo cerrado de reglas, correspondencia regla/categoría, etiquetas agregadas, coordenadas, fragmentos, procedencia y relaciones de transformaciones. Las evidencias de un hallazgo deben pertenecer al rango de esa misma invocación. No se aceptan evidencia huérfana, transformaciones ajenas o no verificadas, ni valores recuperados sin una transformación local que los respalde. La validación JSON comprueba coherencia y trazabilidad, no vuelve a ejecutar las reglas para certificar un payload modificado arbitrariamente.

La correspondencia regla/categoría también se exige en los indicios. Una entrada rechazada no puede atribuirse trabajo, operaciones o bytes de detección. Agotar la profundidad del extractor, incluso al dividir un pipeline, informa `max_expression_depth` y `partial`; no se completa silenciosamente con un resultado vacío.

Errores de tipo/configuración/metadatos producen TypeError, ValueError o ValidationError. Sintaxis no soportada, entradas rechazadas y cotas producen resultados estructurados. `rejected` no contiene hallazgos ni copia una entrada excesiva o Unicode inválido. Los modelos congelan campos, pero las listas no son profundamente inmutables; un consumidor debe revalidar cualquier payload que modifique.

## 6. Trazabilidad y política estricta

Solo se citan piezas efectivamente utilizadas por las condiciones de la regla. No se rellena el contexto con una URL suelta, un valor esperado o una referencia del equipo. La consulta de un valor recuperado exige coincidencia de capa y rango con una transformación verificada de 1A. El vínculo con la definición de una variable se conserva a través de las dependencias de esa transformación, sin inventar enlaces nuevos.

Los offsets conservan la convención de 1A: puntos de código Unicode de Python, inicio en 0, final exclusivo, líneas/columnas en 1. El original no se normaliza. Para una evidencia de L1/L2, `source` indica su posición local y `root_source` el argumento Base64 de L0 como ancla de derivación. No significa que la expresión decodificada exista literalmente en L0. La evidencia cita además la transformación productora de la capa.

Ejemplos reales de las regresiones, usando el texto histórico sin normalizar:

- P4: F0001/B03 cita la escritura de L0 `[135,207)`, línea 4. E0002 cita `$a` en `[158,160)`, con valor recuperado de la clave Run y `T0004`; esa transformación depende de su definición. E0003/E0004 enlazan nombre y valor mediante T0005/T0006. Ninguna cadena aislada justifica B03.
- P6: F0001/B02 cita IEX en L1 `[0,102)` y su entrada DownloadString. F0002/B01 cita la descarga de L1 `[4,102)`. Ambos comparten E0003 (receptor recuperado por T0002) y E0004 (URI recuperada por T0003). Las evidencias de L1 citan T0001, productor de la capa; su ancla original es L0 `[42,314)`. La descarga no genera B06 ni el lanzador B02.

## 7. Deduplicación

La identidad de una operación es `(layer_id, start, end)`, no su texto. La extracción visita cada invocación una vez y las reglas deduplican por `(behavior_id, layer_id, start, end)`. Una operación literal que usa varias recuperaciones genera un hallazgo con contexto; no se vuelven a analizar cadenas recuperadas como scripts autónomos. Las evidencias con igual rol, ubicación, valor y transformaciones se comparten cuando apoyan varios hallazgos.

Las capas de script de 1A representan invocaciones EncodedCommand: el lanzador no se cuenta como el comportamiento interior. Dos lanzadores distintos con texto decodificado idéntico representan dos sitios de operación y se conservan. Tampoco se unen dos Get-Process en líneas distintas. No se afirma equivalencia semántica entre sitios o capas diferentes solo porque coincidan sus cadenas; sin una relación demostrada se mantienen separados. B01 y B02 relacionados en P5/P6 son comportamientos distintos, no duplicados.

## 8. Restricciones del reconocedor

Se omiten capas con anomalías léxicas fatales, delimitadores inválidos, bloques, funciones, control o terminadores como return/exit/throw. Es deliberadamente más restrictivo que un análisis de flujo: incluso puede omitir una operación anterior a un terminador. Los tokens de control en contextos no distinguidos también pueden causar abstenciones conservadoras. Tras cambios explícitos de alias/módulos o Set/New/Remove-Item, se omite el resto de la capa por posible cambio de resolución de comandos.

Se admiten nombres de comando literales, ciertos nombres reconstruidos con `&`, argumentos estáticos de 1A, pipelines sencillos y subexpresiones de comando entre paréntesis. No se interpreta el resultado de comandos, objetos guardados en variables, subexpresiones `$()`, splatting, arrays, hashtables, invocaciones indirectas complejas, métodos arbitrarios, asociaciones entre sitios lejanos o contenido remoto. Las restricciones de LF/CRLF y Unicode de 1A se mantienen.

Los cmdlets se reconocen por sus nombres estándar; una sesión externa puede haberlos reemplazado o no disponer del módulo. No se comprueba el estado del host, si una ruta existe, si una política impide el cambio o si el código llega a ejecutarse. Esos son posibles límites semánticos/falsos positivos de interpretación, distintos de los negativos sintácticos cubiertos. La ausencia de hallazgos nunca significa que un script sea seguro.

## 9. Recursos y seguridad

No hay evaluación de código Python, PowerShell o .NET; no se lanzan procesos, se abren rutas de la entrada, consultan credenciales ni contactan endpoints. Los imports y llamadas del servicio se inspeccionan por AST; las pruebas también bloquean lectura de archivos, procesos y sockets durante un análisis adversario inerte. `urllib.parse.urlsplit` solo analiza texto, no realiza solicitudes.

Se reutilizan las cotas de entrada, tokens, profundidad, valor, volumen y trabajo de 1A. La detección tiene un presupuesto separado con los mismos límites de trabajo/artefactos: la cota total del flujo es la suma de ambas etapas, no un único presupuesto compartido. Por defecto, cada etapa dispone de 4 000 000 unidades de trabajo y 2 MiB acumulados; el original está limitado por separado. No es una garantía de RAM total, tiempo de reloj o sandbox.

`DetectionLimits` añade topes por defecto de 512 operaciones, 256 hallazgos, 128 indicios y 1024 evidencias; sus máximos configurables son 4096/2048/1024/8192. Los wrappers declarados se acotan por operaciones. Al alcanzar una cota se conservan los hallazgos previos y se informa `partial`/`limits_hit`. La evidencia de un hallazgo se incorpora de forma transaccional: un límite no deja piezas huérfanas. No hay timestamps ni decisiones basadas en reloj en la salida.

## 10. Pruebas y resultados P1–P8

La base inicial de implementación fue de **274 pruebas**; la primera entrega de 1B añadió **159**, con **433 aprobadas**. La auditoría añade **55** regresiones/controles: **488 aprobadas, 0 fallidas y 0 omitidas**; 214 nuevas en el incremento completo de 1B. El [acta técnica](phase1b_closure.md) registra las correcciones, resultados y condiciones de cierre. Las mediciones de pytest son observaciones de Windows 11/Python 3.13.3, no benchmarks ni garantías.

| Archivo de pruebas | Cobertura |
|---|---|
| test_rules.py | Positivos de las siete categorías como literal, EncodedCommand y comando reconstruido; negativos, comentarios, cadenas inertes, ambigüedades y catálogo |
| test_integration.py | Piloto, multietiqueta, operaciones repetidas, deduplicación, Unicode/CRLF, capas anidadas, relaciones de variables, wrappers y recuperaciones inline |
| test_contract_security.py | Payloads corruptos, procedencias no permitidas, límites, entrada inválida, fuzz determinista, AST y bloqueo de I/O, demo portable |
| test_audit_regressions.py | 55 casos: falsos positivos demostrados, contratos, profundidad, trazas de P3, barreras sintéticas, deduplicación y combinaciones en capas |
| cases.py | Ejemplos propios inertes de desarrollo, sin credenciales reales ni archivos ejecutables |

| Caso | Esperado histórico | Detectado | Interpretación |
|---|---|---|---|
| P1 | B05 | B05 | Get-Process; otras etapas del pipeline quedan fuera del catálogo |
| P2 | B05 | B05 | Capa decodificada, sin B02 por el lanzador |
| P3 | B01 | Ninguno | Abstención/FN esperado: 1A recupera cmdlet/URI, pero Join-Path corta los bindings antes de `& $c`; no hay uso verificado que vincule el comando final |
| P4 | B03 | B03 | Operación de escritura con tres usos de variable verificados |
| P5 | B01+B02 | B01+B02 | Relación inmediata descarga → evaluador |
| P6 | B01+B02 | B01+B02 | Misma relación sobre L1, con concatenaciones verificadas |
| P7 | B01 | Ninguno | Abstención/FN esperado por OT-FORMAT; sin reconstrucción oculta |
| P8 | B03 | B03 | La instrucción adversaria del comentario es inerte |

Hay seis coincidencias de conjuntos de etiquetas y dos abstenciones/falsos negativos esperados, sin etiquetas adicionales en estos ocho casos. Esto es una regresión del motor nuevo, no una reevaluación de Qwen ni una modificación de las métricas v1. No se reportan precision/recall/F1 globales o por categorías a partir de esta tabla: B04/B06/B07 no tienen positivos en ella y el piloto no es un conjunto de prueba independiente del desarrollo.

Una pasada de desarrollo de estos ocho textos observó llamadas de aproximadamente **0,62–2,80 ms** por caso con imports ya cargados; una única observación, sin control de carga ni caracterización de hardware, no permite estimar rendimiento general. La salida del analizador no incluye esos tiempos para conservar determinismo.

## 11. Demostración y reproducción

Desde la raíz, con el entorno existente:

```powershell
.\.venv\Scripts\python.exe -B experiments\demo_behavior_detection.py
$phase1bTemp = Join-Path $env:TEMP ('powershell-insight-phase1b-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests --basetemp "$phase1bTemp" --tb=short
```

La demo analiza texto propio Get-Process y una descarga inerte a example.com: muestra B01/B05, evidencias y limitaciones como JSON por stdout. No escribe resultados; la prueba también la ejecuta desde un directorio ajeno. Los comandos ejecutan Python, nunca los textos PowerShell. `-B` y `no:cacheprovider` evitan bytecode/caché en el repositorio; los temporales de pytest se crean fuera de él. No se eliminaron archivos ni se instalaron dependencias.

## 12. Evaluación y siguiente integración

Las pruebas comprueban etiquetas esperadas por diseño, positivos/negativos/abstenciones y evidencia suficiente/insuficiente en cada categoría. Se incluye multietiqueta y se comprueba que una descarga no se duplica como B06. Los ejemplos se usaron para construir o revisar las reglas: son desarrollo/regresión, **no held-out ni una evaluación final de generalización**. Los casos P1–P8 siguen siendo piloto separado y solo se consultan desde pruebas.

El servicio prepara la parte determinista de la futura configuración A, pero no se ejecutó el experimento A/B/C ni se comparó con B o C. Antes de una evaluación final se necesitan bases/familias propias, particiones independientes, sintaxis reservada, revisión de equivalencias, congelación de reglas y registro previo del dataset. El generador de variantes y el dataset experimental no se implementan en este incremento de detección. Si se calculan métricas futuras, deberán separar TP/FP/FN por etiqueta y definir explícitamente denominadores para categorías ausentes y micro/macro-F1.

La integración posterior debe consumir el resultado completo con evidencias, abstenciones, versiones y procedencia, no solo etiquetas. No debe convertir un `partial` en ausencia confirmada ni un indicio en hallazgo. La Fase 2 está bloqueada por la selección definitiva del LLM: Qwen2.5-Coder 7B no aprobó el piloto v1 y solo es candidato provisional. La selección requiere una evaluación posterior con casos nuevos, sin sobreajustar P1–P8. No se implementan prompts, API, React, riesgo, STIX ni servicios externos.

La reproducción en Linux sigue pendiente y no bloquea esta implementación. Se mantiene la limitación histórica de identidad binaria al regenerar derivados con saltos de línea dependientes del sistema; no se tocó el evaluador. Las comprobaciones de hashes, anotaciones, fuentes históricas y filtros Git de las fases anteriores siguen incluidas en las 488 pruebas.

## 13. Inventario e integridad de entrega

Nuevos (14, incluida la preparación del cierre):

- backend/app/schemas/behavior_detection.py
- backend/app/services/behavior_detection/__init__.py
- backend/app/services/behavior_detection/extraction.py
- backend/app/services/behavior_detection/rules.py
- backend/app/services/behavior_detection/engine.py
- backend/tests/behavior_detection/__init__.py
- backend/tests/behavior_detection/cases.py
- backend/tests/behavior_detection/test_rules.py
- backend/tests/behavior_detection/test_integration.py
- backend/tests/behavior_detection/test_contract_security.py
- backend/tests/behavior_detection/test_audit_regressions.py
- experiments/demo_behavior_detection.py
- docs/behavior_detector.md
- docs/phase1b_closure.md

Modificados (3): [architecture.md](architecture.md), [roadmap.md](roadmap.md) y [README.md](../README.md), únicamente para describir lo implementado y el estado actual. Se conserva el acta y la documentación histórica de 1A y 0B. No cambian `.gitattributes`, dependencias, metodología, taxonomía, desofuscador ni pruebas previas. Git queda en develop con cambios locales sin staging, para revisión del responsable; no se ejecutaron add, commit, push, merge, rebase, reset ni clean.
