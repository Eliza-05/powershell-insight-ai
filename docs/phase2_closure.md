# Entrega técnica de Fase 2 — LLM provisional

**Fecha: 2026-11-02, America/Bogota.** Integración A/B/C implementada y verificada a nivel
de software. Se completó la comprobación real de transporte/contrato con Qwen3.5 dentro del
presupuesto autorizado, con rechazos y limitaciones registrados. **No se declara éxito de
calidad del LLM ni aceptación semántica integral del sistema.** El modelo mantiene defectos
graves y sigue provisional; la validación científica y la evaluación final siguen pendientes.

## 1. Implementación y alcance

Se entregan servicios Python reutilizables, CLI, contratos estrictos, política común B/C,
contextos aislados, adaptador HTTP local, procedencia de evidencias, control de recursos,
serialización, métricas, pruebas y documentación. Se reutilizan los motores 1A/1B sin cambiar
sus bytes. No se implementaron FastAPI/React ni se inició la Fase 3.

La decisión prospectiva **DEV-03**, concedida por el responsable en la solicitud de esta
entrega, exceptúa exclusivamente la dependencia de desarrollo: construir software antes de
terminar la validación del LLM. La justificación y sus límites están en
[phase2_integration.md](phase2_integration.md). Las actas previas no se modifican.

## 2. Arquitectura técnica

`AnalysisService` separa entrada, motores deterministas, construcción de contexto, inferencia,
validación y resultado. `OllamaAdapter` implementa una interfaz sustituible con transporte,
sampler y exclusión inyectables. Pydantic define `PipelineResult`, `ComparisonResult` y
`ModelReport`; los enums reutilizan la taxonomía existente. La serialización revalida un
snapshot y exige creación exclusiva de archivo. No se depende de los ejecutores del piloto.

## 3. Flujos A/B/C

| Configuración | Entrada y procesamiento | Atribución |
|---|---|---|
| A | Original → 1A → 1B → contrato | Hallazgos/reglas deterministas; riesgo desconocido |
| B | Original → mismo prompt/modelo → validación | Predicciones del LLM; ninguna evidencia de 1A/1B enviada |
| C | Original → 1A → original + trazas permitidas → mismo LLM → validación | Predicciones del LLM con recuperación 1A; sin etiquetas/decisiones/riesgos de 1B |
| ABC | Tres ejecuciones independientes sobre el mismo hash | UUID/resultados separados; ninguna métrica de calidad deducida |

A no consulta Ollama. B/C hacen peticiones separadas, dos mensajes nuevos, sin respuestas
anteriores ni estado conversacional compartido. Concurrencia bloqueada incluso entre procesos
de la aplicación. El procesamiento sigue siendo estrictamente estático.

## 4. Archivos creados y modificados

Código nuevo:

- `backend/app/schemas/pipeline.py`.
- `backend/app/services/pipelines/__init__.py`, `__main__.py`, `config.py`, `context.py`,
  `policy_v1.md`, `resources.py`, `ollama.py`, `validation.py`, `service.py`, `serialization.py`.
- `backend/tests/pipelines/test_pipelines.py` y `test_transport_resources.py`.
- `experiments/check_phase2.py`.

Documentación nueva: este informe y [phase2_integration.md](phase2_integration.md).
Actualizados: `README.md`, `docs/architecture.md`, `docs/roadmap.md`. README/roadmap ya
tenían cambios del usuario al comenzar; se mantuvieron y se actualizaron sus estados actuales.

Evidencia nueva bajo `artifacts/phase2/`: inventario previo, estado local inicial, tres carpetas
`functional_01/02/03`, resumen de seis inferencias, JUnit y verificación/inventario final.
Cada carpeta funcional conserva fuente, A, estado antes/después, intención B/C, peticiones,
respuestas completas, memoria, errores y resumen. Son ejemplos propios de desarrollo.

El [inventario exacto con hashes](../artifacts/phase2/delivery_inventory.json) identifica todos
los archivos de esta entrega. Los archivos previamente existentes del piloto, aunque algunos
ya eran untracked al comenzar, no se reclasifican como creados por Fase 2.

## 5. Pruebas automatizadas

**Pasada final: 841 aprobadas, cero fallidas, cero errores y cero omitidas, en 12,83 s**:
731 regresiones previas y 110 pruebas nuevas. [JUnit](../artifacts/phase2/tests.xml).
La línea base correcta había pasado sus 731 pruebas en 4,12 s. Una invocación inicial sobre
el directorio temporal compartido produjo 27 errores de fixtures por permisos, resueltos
usando el entorno `.venv` y un `--basetemp` nuevo; no se cambiaron pruebas históricas.

Cobertura nueva: A sin inferencia/contexto/estado de Ollama; B original; C con 1A sin detector;
igualdad de política, modelo, digest/opciones/esquema B/C; comparación; cero/una/múltiples
etiquetas; B02 funcional y negativos EncodedCommand/Get-Credential/cadenas/bloques; incertidumbre,
inyección como datos, evidencia falsa/ambigua/origen incorrecto, reconstrucciones no verificadas,
JSON/esquema inválidos, UTF-8 inválido, claves duplicadas/no finitos, truncamiento, thinking
inesperado, tool calls, conteos de tokens, servicio apagado, modelo/digest incorrectos, recursos,
OOM, timeout/cancelación, tamaños, exclusión entre procesos, circuit breaker, aislamiento,
persistencia/CLI, red fija loopback y ausencia de ejecución de muestras.

Los servidores HTTP de pruebas son sintéticos; **Pytest no invoca el modelo**. Las pruebas
con mocks no prueban exactitud semántica de Qwen3.5. El procedimiento reproducible está en
[la guía](phase2_integration.md#seguridad-y-pruebas).

## 6. Ollama real: seis inferencias, ningún reintento

Digest instalado verificado antes de las pruebas y en cada petición:
`d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
Ollama local 0.40.13; único modelo usado `qwen3.5:4b-q4_K_M`; CPU, contexto 8192,
salida máxima 2048, temperatura 0, seed 42, `think=false` y `truncate=false`.
Los residentes posteriores confirmaron el digest, contexto y `size_vram=0`.
La presencia de Qwen2.5 en el inventario instalado no implicó ejecución: no se cargó ni usó.

Política común `application-analysis-v1`, SHA-256:
`b4202d0ecfb2697b7476804ce757970f0c76aaf55c81e5e99d34ebc4e6bceb1a`.
Los seis payloads conservaron este hash y las mismas opciones. No se cambió el prompt entre
comprobaciones ni se repararon respuestas. Se consumió todo el presupuesto: **6/6**.

| Ejemplo propio nuevo | B | C | Duraciones B / C |
|---|---|---|---|
| `functional_01`: EncodedCommand de `Get-Process -Id 92047` | `completed` estructural | `error`: cita atribuida a T0001, pero el fragmento está en original, no en su texto recuperado | 38,794 / 39,527 s |
| `functional_02`: salida de concatenación literal | `completed` estructural | `error`: riesgo benigno con incertidumbre media; la cita también confunde texto original/recuperado | 33,074 / 34,790 s |
| `functional_03`: comando con variable desconocida | `completed` estructural | `partial`: recuperación no resuelta conservada; reporte aceptado estructuralmente | 23,802 / 40,140 s |

[Resumen íntegro](../artifacts/phase2/functional_summary.json),
[primera comprobación](../artifacts/phase2/functional_01/summary.json),
[segunda](../artifacts/phase2/functional_02/summary.json),
[tercera](../artifacts/phase2/functional_03/summary.json).

`completed` no significa etiqueta correcta: B inventó una decodificación en el primer ejemplo,
atribuyó B02 a mera concatenación en el segundo y B01 a un destino desconocido en el tercero.
El último C también atribuyó B02 sin un destino funcional determinado y escribió prosa en
`recovered_content`. Estas salidas permanecen como **afirmaciones sin revisión semántica**,
no como hechos verificados. Son observaciones técnicas de desarrollo, no adjudicación humana
independiente ni tasas de precisión/F1/aceptación científica.

La ruta real C de envío de recuperación no vacía fue comprobada, pero las dos respuestas de
esos ejemplos fueron rechazadas; **no se obtuvo una respuesta C aceptada que citara correctamente
texto recuperado no vacío**. Ese recorrido de éxito y su trazabilidad se validan con mocks.
Se registra esta limitación; no se reemplazan fallos con el último caso ni se ocultan intentos.

## 7. Seguridad comprobada

Muestras y recuperaciones solo como texto; no se ejecutaron PowerShell, Base64, IEX ni código
del modelo; no se visitaron URLs de muestras ni se lanzaron procesos con sus textos como
argumentos. El código nuevo de servicio no importa subprocess ni usa eval/exec. Los subprocess
de la suite ejecutan únicamente Python de pruebas/CLI y verifican locks, con archivos de texto
como entrada leída. El transporte de aplicación solo admite loopback y rutas fijas, sin proxies,
redirects, pull ni herramientas LLM. No se cambiaron protecciones, opciones globales o apps.

C nunca recibió el resultado de 1B; las pruebas impiden llamar al detector durante C. No se
leyeron datasets/anotaciones en los constructores de contexto. No se reejecutó el piloto ni se
usó selección para ajustar el prompt. Los originales/respuestas se guardan solo por petición
explícita del consumidor o por el harness funcional autorizado.

## 8. Memoria y errores

Mínimos observados durante las seis llamadas: **4,516 GiB de RAM disponible** y
**4,466 GiB de compromiso disponible**. Cero violaciones del margen de 2 GiB; ningún timeout,
OOM o fallo del colector durante estas llamadas. No se atribuye variación global exclusivamente
a Ollama, porque el equipo siguió compartido con otras aplicaciones.

`/api/ps` informó tamaño residente de 3.239.523.121 bytes (~3,02 GiB), CPU y contexto 8192;
ese dato no equivale al compromiso total del árbol de procesos. El monitor nuevo registra
RAM/compromiso del sistema, no working set privado por proceso ni paginación física a disco.

Reservas exigidas: en frío 8 GiB + 2 GiB de margen; cargado en CPU con igual contexto,
1 GiB + 2 GiB. El presupuesto se comprueba también inmediatamente antes del despacho; se
muestrea cada segundo y al terminar. Los contadores y muestras se conservan en cada JSON.
Los límites no se rebajaron y no se cerraron aplicaciones para conseguir margen.

Las pruebas simulan RAM/compromiso insuficiente, fallo de monitor, timeout y cancelación;
verifican que B/C fallen con errores estructurados y A continúe. Tras interrupción real de
transporte/recursos el circuito persiste bloqueado hasta revisión explícita del estado local;
no se presume que cerrar el socket terminó inmediatamente la inferencia del servidor.

## 9. Limitaciones y defectos registrados

| ID | Hallazgo | Estado / tratamiento |
|---|---|---|
| P2-LLM-01 | Decodificaciones y efectos inventados, falsa asociación B02/obfuscación | Abierto: defecto grave de calidad del modelo provisional; prompts instructivos no lo eliminan |
| P2-LLM-02 | Citas con fuente incorrecta y riesgo/uncertidumbre incoherentes | Rechazo efectivo en C01/C02; respuestas originales conservadas |
| P2-LLM-03 | Etiquetas contradicen la explicación; prosa presentada como reconstrucción | Abierto: ni esquema ni presencia literal certifican semántica; revisión posterior obligatoria |
| P2-VAL-01 | Una cita existente puede respaldar una afirmación falsa | Límite declarado en cada resultado; no se usa detector 1B como oráculo para ocultarlo |
| P2-CTX-01 | Cota por bytes rechaza contextos que un tokenizador exacto podría admitir | Decisión conservadora explícita; sin recorte silencioso ni tokenizer adicional instalado |
| P2-OPS-01 | Clientes Ollama externos no comparten el lock; muestreo no reserva RAM | Requiere uso local exclusivo durante inferencia; no hay control global de apps |
| P2-REAL-01 | No hubo salida real C aceptada con cita correcta de recuperación no vacía | Flujo enviado y rechazos comprobados; éxito de procedencia cubierto con mocks; no se finge comprobación positiva |

No se identificaron defectos críticos nuevos del software sin registrar. El catálogo parcial
de 1A/1B y sus FN aceptados no se amplió; ver [guía y límites](phase2_integration.md).
Las últimas mejoras de registro y revisión de reserva quedaron verificadas por pruebas
automatizadas; no se añadieron inferencias después de consumir el presupuesto de seis.

## 10. Estado técnico real

**Implementación técnica de Fase 2 completada con LLM provisional, con los límites anteriores.**
Los tres pipelines y la comparación existen, A es independiente, las 841 pruebas pasan,
B/C despachan realmente al modelo y procesan éxitos estructurales y rechazos sin reparar datos.
La memoria permitió las llamadas: no corresponde afirmar que la prueba real quedó pendiente
por hardware. Tampoco corresponde declarar éxito semántico integral: P2-REAL-01 y los defectos
de calidad permanecen registrados. Esta entrega cierra el software autorizado sin convertir
esas obligaciones pendientes en una nueva subfase ni en aprobación automática del candidato.

## 11. Estado científico separado

Piloto v2 **PENDIENTE / INCONCLUSO**, 58 intentos históricos y 68 llamadas de selección pendientes;
no se suman a sus métricas las seis inferencias funcionales. r0/r1, umbrales, hashes e incidencia
de memoria se conservaron. No se cambió el criterio de aceptación, se aprobó el modelo ni se
demostró H1/H2. El uso provisional no autoriza por sí solo continuar selección o evaluación final.

## 12. Preparación para Fase 3 y Fase 4

Fase 3 puede consumir el servicio síncrono desde un worker acotado y generar contratos de API/UI
desde Pydantic. Debe conservar estados, errores, procedencia, advertencias y autoría del riesgo,
escapar código y separar una respuesta operativa de un resultado científico. Endpoints, React,
retención de datos y experiencia web siguen sin implementarse por alcance expreso.

Fase 4 requiere decisión metodológica sobre el modelo, datos/familias independientes con
anotaciones y revisión, particiones y componentes congelados, hardware/contexto controlados,
adjudicación semántica y métricas exploratorias transparentes. No reutilizar estas pruebas
ni la selección interrumpida como evaluación final independiente.

## 13. Git e integridad

Rama **develop**, todo local y sin staging. No se ejecutaron `git add`, `commit`, `push`,
`merge`, `rebase`, `reset --hard` o `clean`; no se modificó índice ni historial. La comprobación
del SHA-256 de `.git/index` confirma identidad con el inicio. `git diff --check` pasó.

La comparación con el inventario previo confirma que los únicos archivos previamente
inventariados modificados fueron `docs/architecture.md` y `docs/roadmap.md`, además de README
(actualizado intencionalmente, fuera del inventario previo por directorios). No falta ningún
artefacto previo: motores, pruebas históricas, datasets, prompts, congelaciones, umbrales,
resultados y documentos históricos del piloto conservan sus bytes. Los numerosos untracked
previos permanecen para revisión del propietario, separados del inventario nuevo de Fase 2.

Evidencia verificable: [recibo final](../artifacts/phase2/final_verification.json),
[inventario nuevo](../artifacts/phase2/delivery_inventory.json),
[inventario previo](../artifacts/phase2/before.json).
