# Fase 1B — Aprobación técnica y cierre formal

**Estado:** **APROBADA TÉCNICAMENTE Y CERRADA FORMALMENTE**, dentro del subconjunto de detección documentado, mediante autorización expresa del responsable en esta conversación. Publicación pendiente a cargo del propietario. La Fase 2 sigue bloqueada por la selección definitiva del LLM y no se inicia.

**Responsable:** Responsable del proyecto, identificado por el rol y la autorización recibida; no se dispone de un nombre personal verificado. Fuente: mensaje «Aprobación y cierre formal de la Fase 1B», que declara «Apruebo técnicamente la Fase 1B dentro del subconjunto de detección documentado». No se registra nombre personal, firma ni una revisión independiente del código que no haya ocurrido.

La autorización reconoce las doce reglas parciales B01–B07, la integración con 1A, evidencias y deduplicación, los siete grupos de defectos corregidos, las 488 pruebas aprobadas, la integridad histórica y el análisis exclusivamente estático. Acepta las abstenciones de P3 y P7 como limitaciones y exige mantenerlas como falsos negativos frente al ground truth. No autoriza nuevas funciones, pilotos, inferencias, descargas de modelos o inicio de la Fase 2.

## 1. Objetivos y alcance real

Se implementó `analyze_behaviors` para analizar texto PowerShell sin ejecutarlo, integrar las recuperaciones verificadas de 1A y producir B01–B07 con evidencias, relaciones contextuales, indicios separados y límites. Hay doce reglas de subconjuntos, no un clasificador de malware/riesgo ni cobertura completa del lenguaje. El contrato y el catálogo están en [behavior_detector.md](behavior_detector.md).

La auditoría partió de develop, con los 15 archivos locales previstos de 1B: tres documentos versionados modificados y doce nuevos, todos sin staging. La base reportada se reprodujo: 433 pruebas aprobadas. Se revisaron detector, contratos, pruebas, taxonomía, metodología, seguridad, roadmap y la interfaz de trazabilidad/recuperación de 1A. Se identificaron problemas concretos antes de modificar producción. No se amplió el catálogo ni se implementó OT-FORMAT ni se cambió la metodología experimental.

## 2. Arquitectura implementada

| Componente | Responsabilidad |
|---|---|
| schemas/behavior_detection.py | Versiones, límites y validación de hallazgos, evidencias, indicios y referencias |
| behavior_detection/extraction.py | Reconocedor acotado de invocaciones y argumentos sobre el lexer de 1A |
| behavior_detection/rules.py | Doce reglas con condiciones positivas, negativas y evidencia mínima |
| behavior_detection/engine.py | Integración, presupuestos, construcción atómica de evidencia y deduplicación |
| behavior_detection/__init__.py | API Python pública |
| tests/behavior_detection/ | Ejemplos propios inertes y pruebas de implementación/auditoría |
| experiments/demo_behavior_detection.py | JSON por stdout con un ejemplo inerte, sin interfaz ni servicios |

Se conservan el lexer, separador `_statements`, presupuestos y desofuscador de 1A. El uso de un helper interno está documentado y cubierto por regresiones. El detector no recalcula valores de variables o concatenaciones: consulta transformaciones verificadas en el sitio de uso. No se añadieron dependencias. La organización actual permite separar extracción, condiciones y trazabilidad sin una refactorización extensa.

## 3. Reglas B01–B07 y cobertura parcial

| Categoría | Reglas revisadas | Evidencia exigida y límites |
|---|---|---|
| B01 | WEBGET, WEBCLIENT | Invocación de GET o DownloadString/DownloadFile y URI HTTP(S) vinculada. WebClient exige receptor inmediato explícito; DownloadFile también destino. Sin URI aislada, métodos/receptores desconocidos o puerto inválido |
| B02 | IEX | Evaluador invocado y entrada estática no vacía o DownloadString inmediato relacionado. No EncodedCommand ni `&` por sí solos; wrappers declarados excluidos, procedencia desconocida indicada |
| B03 | RUNWRITE | Escritura New/Set-ItemProperty y ruta de proveedor inequívoca Run/RunOnce, nombre y valor. Sin lecturas, menciones, rutas relativas o tipo no textual. No tareas, servicios, WMI o Startup |
| B04 | DEFENDER-DISABLE, DEFENDER-EXCLUSION, FIREWALL-DISABLE | Booleano que debilita la defensa o exclusión explícita; perfil de firewall conocido cuando se declara. No consulta o restauración; sin prueba de éxito en el host |
| B05 | HOSTQUERY, RUNQUERY | Cmdlet de consulta en posición de comando; la lectura de Run cita también la ruta. No términos dentro de datos inertes ni intención maliciosa |
| B06 | HTTP-SEND, CONNECTIVITY | Envío POST/PUT/PATCH con URI/cuerpo o Test-NetConnection con destino. GET no aporta B06. Sin inferir exfiltración/C2 ni interpretar toda respuesta como descarga |
| B07 | STORED-CREDENTIAL | Get-StoredCredential con target estático, como solicitud de acceso al almacén. No Get-Credential, palabras password/token ni resultados desconocidos de comandos |

Los IDs completos conservan el prefijo `BD-Bxx-` y el catálogo `static-behaviors-v1`. Cada regla tiene positivos, negativos, evidencia mínima y limitaciones en código/documentación; las siete categorías tienen pruebas sintéticas. Las correcciones restringen falsas confirmaciones, sin añadir familias nuevas de comportamiento. Get-StoredCredential presupone el cmdlet del módulo CredentialManager: no comprueba instalación, autorización ni presencia de la credencial, ni implica malicia.

## 4. Resultados finales P1–P8

Ground truth histórico y resultados del detector se mantienen separados. «Abstención» no se contabiliza como verdadero positivo.

| Caso | Ground truth | Detectado | TP | FP | FN | Abstención sobre lo esperado |
|---|---|---|---|---|---|---|
| P1 | B05 | B05 | B05 | — | — | No |
| P2 | B05 | B05 | B05 | — | — | No; lanzador sin B02 |
| P3 | B01 | Ninguno | — | — | B01 | Sí |
| P4 | B03 | B03 | B03 | — | — | No |
| P5 | B01+B02 | B01+B02 | B01+B02 | — | — | No |
| P6 | B01+B02 | B01+B02 | B01+B02 | — | — | No |
| P7 | B01 | Ninguno | — | — | B01 | Sí |
| P8 | B03 | B03 | B03 | — | — | No; comentario adversario inerte |

Resumen descriptivo de estas regresiones: seis coincidencias exactas de conjuntos, ocho etiquetas TP, cero FP y dos FN. P3/P7 son dos abstenciones y dos falsos negativos respecto de B01, aunque estén justificadas por la cobertura. No se cambian los resultados de Qwen/piloto v1 ni se reclasifican los casos para mejorar el agregado. B04/B06/B07 no tienen positivos en P1–P8; sus pruebas se realizan con ejemplos sintéticos separados.

El piloto se conoce y se utiliza como regresión, no como validación ciega. Los ejemplos sintéticos también se usan para desarrollar/auditar reglas: no se presentan como prueba independiente final ni como evidencia de superioridad A/B/C. No se calculan aquí precision/recall/F1 de generalización.

## 5. Investigación prioritaria de P3 y contraste con P7

### P3: recuperación correcta, barrera conservadora intencional

La interfaz entrega al detector el resultado completo de 1A. Se comprobaron estas transformaciones, sin leer referencias o etiquetas durante producción:

| IDs de 1A | Contenido y estado |
|---|---|
| T0001/T0002 | Concatenación de la URI y definición de `$u`: success; T0002 depende de T0001 |
| T0003/T0004 | Concatenación del nombre del cmdlet y definición de `$c`: success; T0004 depende de T0003 |
| T0005 | Uso de `$env:TEMP`: failed; no valor de entorno consultado |
| T0006 | Concatenación report.csv del argumento de Join-Path: success |
| T0007 | Uso posterior de `$c` en la invocación: failed, sin contenido recuperado |
| T0008 | Uso posterior de `$u`: failed, sin contenido recuperado |
| T0009 | Uso posterior de `$destino`: failed, sin contenido recuperado |

En `deobfuscation.engine._Recovery.analyze_layer`, analizar el RHS Join-Path produce una expresión no pura/no recuperable. Se borran los bindings y se deshabilita la propagación posterior en esa capa. La política es general para resultados de comandos, no específica de Join-Path o P3. Así se pierde deliberadamente la certeza de uso posterior, no el texto de las definiciones.

El detector indexa solo cadenas y usos de variable `success`/verificados por su capa y rango. T0002/T0004 son definiciones anteriores, no pruebas del valor en T0007/T0008. Por ello no interpreta `$c` como Invoke-WebRequest en la llamada final ni enlaza `$u` con la URI anterior. El resultado conserva los artefactos previos y los diagnósticos, sin hallazgo ni evidencia afirmativa.

No se identificó un defecto de integración en esta abstención. El nombre Join-Path puede resolver a una función de la sesión y no se han demostrado sus efectos en el ámbito llamador. Una excepción basada solo en su nombre o en que no se ve otra asignación ignoraría precisamente esa incertidumbre. Tampoco puede sustituirse por la referencia manual ni usar la etiqueta esperada. No se introdujo una whitelist de pureza ni se cambió 1A.

La falta de valor de OutFile por sí sola no es la razón determinante: B01 necesita la operación y su URI vinculadas. Aquí los usos de ambos valores esenciales han dejado de estar verificados. Reconocer este caso exigiría ampliar explícitamente el contrato de flujo/pureza y probarlo con negativos y resolución de comandos, trabajo fuera de esta auditoría. Se conserva la abstención y el FN.

Las nuevas regresiones cambian nombres, valores y URI: una invocación antes de una barrera sí produce B01; tras Join-Path, un comando desconocido o Set-Variable no se resucitan los bindings antiguos. También se verifica que una reasignación no se trate como asignación única.

### P7: OT-FORMAT fuera de alcance

1A detecta tres expresiones OT-FORMAT `unsupported`, sin cadenas resultantes. El detector no formatea ni usa el original manual para completar la operación. OT-FORMAT figura entre las técnicas que obstaculizan el análisis; no se detecta B01. Se conserva el FN y la abstención, sin modificar el ground truth o el alcance de 1A.

## 6. Evidencias y trazabilidad

Se verificaron las porciones literales, offsets, capas, raíces y referencias de P4/P5/P6, además de Unicode/CRLF y capas anidadas sintéticas. La convención sigue siendo puntos de código Python, inicio en 0 y final exclusivo; líneas/columnas en 1.

- **P4:** B03 en L0 `[135,207)`, línea 4. E0002/E0003/E0004 citan los usos `$a`/`$b`/`$d` y T0004/T0005/T0006, que dependen de sus definiciones. La ruta, nombre y valor están relacionados con esa escritura, no con otra operación.
- **P5:** B02 cita L0 `[0,83)` y su entrada DownloadString; B01 cita la descarga `[4,83)`. Se comparten las citas del receptor y URI. Los rangos existen en el original recibido.
- **P6:** B02 cita L1 `[0,102)` y B01 L1 `[4,102)`. Las evidencias de L1 incluyen T0001, que produjo la capa; el tipo y URI reconstruidos citan T0002/T0003. `root_source` apunta a L0 `[42,314)`, el argumento Base64, no a una posición literal ficticia de IEX en L0.

Las evidencias de capas/valores recuperados mantienen `deobfuscator_recovered`. El servicio solo admite procedencia de entrada original/variante y no acepta un resultado de recuperación arbitrario del llamador. No hay lecturas de referencias manuales, ground truth o salida del modelo en producción. La validación JSON rechaza rangos, fragmentos, raíces, valores, referencias y enlaces entre operaciones incoherentes; no certifica la semántica de un payload arbitrariamente reescrito.

Un hallazgo respaldado puede existir en un resultado global partial, por ejemplo P5/P6, porque la gramática de 1A no comprende toda la expresión. Se comunica la limitación global sin convertir en confirmado un candidato cuyos argumentos requeridos son desconocidos.

## 7. Deduplicación

La clave es comportamiento + capa + rango de la operación. Se verificaron:

1. Una operación original con URI/nombre reconstruidos produce un solo hallazgo con varias citas; los valores recuperados no se vuelven a escanear como scripts.
2. Dos descargas a destinos diferentes generan dos operaciones, aunque compartan B01.
3. Dos escrituras de persistencia con sitios/nombres distintos se conservan.
4. Una escritura o descarga con múltiples evidencias mantiene un solo hallazgo; no hay evidencias huérfanas.
5. B01 y B02 de una relación descarga → IEX se conservan como dos comportamientos, compartiendo citas útiles.
6. Dos capas EncodedCommand anidadas con una única operación interior no multiplican el hallazgo por cada representación intermedia.

Dos lanzadores independientes con payload idéntico tienen sitios de operación distintos y se conservan. No se fusionan capas o sitios por igualdad textual: sin prueba de equivalencia, esa fusión sería injustificada. No hay una demostración general de equivalencia semántica ni seguimiento completo de objetos/flujo.

## 8. Seguridad y recursos

Se revisó el recorrido texto → 1A → lexer reutilizado → invocaciones → reglas → evidencias → JSON. No hay ejecución PowerShell/.NET/Python del contenido, llamadas dinámicas, lectura de sus rutas, acceso a credenciales reales o conexiones a sus destinos. Las pruebas de AST y bloqueo de archivos/procesos/sockets permanecen aprobadas. La consulta a documentación técnica se realizó fuera del flujo de análisis y no derivó de destinos del script.

Se mantienen cotas de tamaño, profundidad, tokens, operaciones, hallazgos, evidencias, indicios, volumen y trabajo. La detección tiene un presupuesto separado de 1A; se acotan ambas etapas y se informa cada contador, sin afirmar que compartan una sola bolsa. Los metadatos de wrappers también se limitan. Un límite devuelve partial y conserva los hallazgos anteriores; la construcción atómica no deja evidencias sin consumidor. El límite de profundidad del extractor ahora se comunica explícitamente.

Los máximos configurables siguen teniendo techos. No se encontró una ruta de ejecución o de acumulación ilimitada; las cotas no equivalen a un límite exacto de RAM, latencia o sandbox de proceso. La validación, índices y objetos Python tienen overhead. Se mantiene la necesidad futura de aislamiento/timeout externo para una interfaz de servicio, sin ejecutar las muestras.

## 9. Defectos demostrados y correcciones

| ID | Defecto previo | Corrección mínima y pruebas |
|---|---|---|
| AUD-1 | Se trataba `(Get-UnresolvedTarget)` como un bareword literal, inventando valores de resultados de comandos y confirmando B02/B03/B04/B06/B07 o método GET sin recuperación | Distinguir modo argumento de expresión tras quitar paréntesis. Solo literales/booleanos/recuperaciones verificadas conservan valor. 14 negativos directos/codificados y control de consulta interior sin B02 |
| AUD-2 | El receptor WebClient se reconocía con New-Object o -TypeName pegados a las comillas, incluso con un salto escapado que no separa argumentos | Exigir separación real en el constructor. Cuatro negativos; positivos previos y P5/P6 conservados |
| AUD-3 | El regex de Run admitía HKCU sin dos puntos y nombres de hive sin proveedor, que pueden ser rutas relativas | Exigir drive HKCU/HKLM con dos puntos o Registry:: con hive completo. Cuatro negativos y cuatro controles de escritura/lectura |
| AUD-4 | Se confirmaba debilitamiento de firewall con perfil desconocido/inválido, sin citarlo; las restauraciones reconocidas recibían además el diagnóstico incorrecto de comando fuera del catálogo | Validar Domain/Private/Public cuando se especifica, incluir su cita y mantener restauraciones sin B04 ni ese indicio. Cuatro negativos, tres controles de contexto/restauración y dos regresiones de diagnóstico |
| AUD-5 | La comprobación HTTP leía hostname pero no validaba un puerto explícito inválido/fuera de rango | Acceder también a port y capturar ValueError. Seis negativos para GET/envío y un positivo con puerto válido |
| AUD-6 | Al llegar a la profundidad del extractor se retornaba silenciosamente, incluso con resultado complete vacío para un pipeline que 1A había aceptado | Lanzar el límite estructurado max_expression_depth. Una regresión verifica partial sin alterar el resultado de 1A |
| AUD-7 | El contrato aceptaba indicios con categoría distinta de su regla y contadores de detección no nulos en un rechazo | Rechazar ambas contradicciones. Un payload de indicio y tres contadores corruptos |

Los problemas se reprodujeron antes de corregir: la primera tanda de 53 casos tuvo 41 fallos esperados y 12 controles aprobados; dos regresiones adicionales reprodujeron el diagnóstico erróneo de restauración. Las siete agrupaciones anteriores no son técnicas nuevas ni modificaciones del desofuscador. Los contratos corruptos describen debilidades de validación de payloads; no se observó que el motor generara esos payloads internamente.

## 10. Resultados exactos de pruebas

| Conjunto | Aprobadas |
|---|---:|
| Fases previas a 1B | 274 |
| Implementación inicial 1B | 159 |
| Auditoría 1B | 55 |
| **Total final** | **488** |

Resultado de la auditoría: **488 aprobadas, 0 fallidas, 0 errores y 0 omitidas**, en **4,03 s** observados. La validación del cierre documental volvió a ejecutar la suite completa: **488 aprobadas en 4,30 s**, sin fallos, errores u omisiones. No se modificó código, reglas o pruebas para registrar el cierre, ni se repitió una auditoría general. Las 55 pruebas de auditoría están en `backend/tests/behavior_detection/test_audit_regressions.py`; incluyen regresiones de los defectos y controles de P3, barreras/reasignaciones, multietiqueta, deduplicación y ruido en capas recuperadas. No se cuenta cada iteración del fuzz existente como una prueba pytest adicional.

Comando de validación desde la raíz, con ruta temporal nueva:

```powershell
$audit1bTemp = Join-Path $env:TEMP ('powershell-insight-audit1b-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests --basetemp "$audit1bTemp" --tb=short
```

Una ejecución auxiliar sin basetemp encontró permisos insuficientes en el temporal predeterminado de pytest; se resolvió usando rutas nuevas fuera del repositorio, sin borrar carpetas preexistentes. Las validaciones finales usan ese procedimiento. El tiempo de pytest es una observación del entorno Windows 11/Python 3.13.3, no una mejora de rendimiento demostrada ni un benchmark. La demo portable/JSON, AST, bloqueo de I/O, contratos y pruebas históricas están incluidas en el total.

## 11. Limitaciones y riesgos restantes

P3 y P7 siguen siendo FN por barreras de flujo y falta de OT-FORMAT. No se prueban alcanzabilidad general, efectos de comandos desconocidos, equivalencia de variantes, estado del host, éxito de una operación ni resolución de nombres en la sesión. Se excluyen conservadoramente bloques/control y se omite el resto de una capa tras cambios explícitos de resolución de comandos. Esto puede causar más falsos negativos.

B03 no cubre todos los mecanismos de persistencia; B07 solo cubre el acceso mediante Get-StoredCredential; B06 no modela toda comunicación, nube o canal DNS. La validación HTTP no es una implementación completa de System.Uri. Un IEX no declarado dentro de una recuperación podría ser un wrapper añadido: su procedencia funcional depende del historial fiable del llamador, no puede probarse por sintaxis. Estas limitaciones están advertidas, sin probabilidades inventadas ni valoración de riesgo.

Persisten riesgos de falsos positivos fuera del subconjunto probado, por ejemplo por cmdlets reemplazados, módulos ausentes, metadatos incompletos o diferencias de contexto/ejecución no modeladas. Las pruebas de desarrollo no garantizan precisión general y no constituyen una evaluación independiente definitiva. La aprobación acepta el alcance parcial y sus límites, no una garantía para scripts arbitrarios.

Los modelos congelados contienen listas mutables; se requiere revalidar payloads alterados. Se mantiene el acoplamiento a helpers internos de 1A, bajo regresiones. En Windows 11/Python 3.13.3 se ejecutaron las 488 pruebas de 1B y la demo portable. La Fase 1A publicada ya se comprobó en tres clones limpios Windows con core.autocrlf=false/true/input y 274 pruebas por clon; eso no equivale a haber clonado una publicación de 1B, todavía pendiente. Linux y la identidad binaria de derivados históricos regenerados en otro sistema siguen pendientes. No se modificó el evaluador ni se ejecutaron nuevos clones o pruebas Linux para este cierre.

## 12. Integridad de Fases 0B y 1A y estado de Git

Se compararon hashes de los archivos presentes al inicio de la auditoría y se conservaron los cambios locales previos. No se alteraron muestras/referencias, manifiestos, anotaciones v0.1/v0.2, prompts, resultados crudos/derivados, SHA256SUMS, metodología, taxonomía, seguridad, código/contratos/pruebas de 1A ni su acta de cierre. Las etiquetas y riesgos históricos permanecen iguales. Las comprobaciones de los 18 hashes registrados, seis resultados v1, fuentes y referencias siguen aprobadas. `.gitattributes` no cambió.

En esta auditoría se ajustaron el esquema de detección, extraction.py, rules.py y engine.py, el documento del detector y los estados de README/roadmap. Se añadieron el módulo de 55 pruebas y este registro. `docs/architecture.md` conserva su cambio previo de implementación de 1B; no requirió corrección adicional. El inventario completo del incremento está en [behavior_detector.md](behavior_detector.md#13-inventario-e-integridad-de-entrega).

Rama develop, sin staging ni operaciones de publicación/historial. El incremento completo pendiente de revisión consta de 17 archivos: tres versionados modificados y catorce nuevos. `git diff --check`, referencias locales e inventario de archivos/ignorados se verificaron. No hay temporales de pruebas en el repositorio fuera de `.venv`; los temporales nuevos permanecen fuera. No se ejecutaron add, commit, push, merge, rebase, reset o clean.

Para el cierre se actualizaron únicamente este registro y los estados documentales de README, architecture, roadmap y behavior_detector. Se volvieron a comprobar los 18 hashes registrados y la identidad de los históricos frente al inicio de esta tarea. El inventario pendiente se revisó para descartar archivos temporales, archivos de credenciales y patrones habituales de secretos; no se detectaron. Esta comprobación de patrones no constituye una garantía universal de ausencia de secretos.

Inventario exacto pendiente de publicación:

| Estado | Archivo |
|---|---|
| Modificado | README.md |
| Modificado | docs/architecture.md |
| Modificado | docs/roadmap.md |
| Nuevo | backend/app/schemas/behavior_detection.py |
| Nuevo | backend/app/services/behavior_detection/__init__.py |
| Nuevo | backend/app/services/behavior_detection/engine.py |
| Nuevo | backend/app/services/behavior_detection/extraction.py |
| Nuevo | backend/app/services/behavior_detection/rules.py |
| Nuevo | backend/tests/behavior_detection/__init__.py |
| Nuevo | backend/tests/behavior_detection/cases.py |
| Nuevo | backend/tests/behavior_detection/test_audit_regressions.py |
| Nuevo | backend/tests/behavior_detection/test_contract_security.py |
| Nuevo | backend/tests/behavior_detection/test_integration.py |
| Nuevo | backend/tests/behavior_detection/test_rules.py |
| Nuevo | docs/behavior_detector.md |
| Nuevo | docs/phase1b_closure.md |
| Nuevo | experiments/demo_behavior_detection.py |

## 13. Criterios de aceptación cumplidos y pendientes

| Criterio | Estado |
|---|---|
| Doce reglas, siete categorías y alcance explícito | Cumplido dentro del subconjunto |
| Integración 1A y política estricta sin referencias/ground truth en producción | Cumplido |
| Evidencias verificables, procedencia, rangos y cadenas de derivación | Cumplido en revisión y pruebas |
| Deduplicación sin colapsar operaciones independientes | Cumplido en los escenarios revisados |
| Positivos, negativos, abstenciones, multietiqueta y contratos | Cumplido; 488 pruebas |
| Seguridad estática y presupuestos | Cumplido en código y pruebas, con límites de RAM/latencia documentados |
| Conservación de históricos y cambios locales sin staging | Cumplido |
| P3/P7 y cobertura completa de PowerShell | No cubiertos; FN y limitaciones explícitos, no criterios falsamente satisfechos |
| Validación independiente final y reproducción Linux | Pendientes; no se afirman realizadas |
| Aprobación técnica y cierre formal por el responsable | Cumplido por autorización expresa de esta conversación |

No quedan defectos reproducidos en la auditoría sin corregir dentro del alcance. **Dictamen: Fase 1B aprobada técnicamente y cerrada formalmente por el responsable**, con P3/P7 como falsos negativos aceptados y las limitaciones documentadas. La aprobación no convierte el piloto en evaluación independiente ni congela el dataset experimental.

## 14. Preparación para la Fase 2

La desofuscación y el detector quedan preparados como componentes de la configuración determinista A: una API Python entrega etiquetas, hallazgos, evidencias, incertidumbre, versiones y límites. No se ejecutó una evaluación comparativa A/B/C ni se afirma que su pipeline experimental completo esté terminado. El dataset/familias, particiones independientes y generador siguen pendientes según el roadmap; cualquier evaluación definitiva deberá fijar sus prerrequisitos y congelar sus componentes.

**Fase 2 bloqueada por la selección definitiva del LLM.** Qwen2.5-Coder 7B no aprobó el piloto v1 y permanece exclusivamente como candidato provisional. Se mantiene DEV-01: la selección deberá basarse en una evaluación posterior con casos nuevos, evitando ajustar el modelo o sus prompts para alcanzar los resultados esperados de P1–P8. La aprobación de 1B no satisface ese prerrequisito ni autoriza iniciar la Fase 2.

No se implementaron LLM, prompts de producción, FastAPI, React o experimento A/B/C. No se ejecutaron nuevos pilotos, inferencias o descargas de modelos. El siguiente paso inmediato es la revisión del inventario y publicación personal por el propietario; no se inicia la Fase 2.
