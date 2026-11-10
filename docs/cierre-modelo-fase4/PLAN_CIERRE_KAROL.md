# Plan de cierre técnico y experimental — Karol

**Proyecto:** PowerShell Insight AI. **Fecha de inspección:** 9 de noviembre de 2026, America/Bogota. **Rama base:** `integration/final-validation`. **Estado de partida:** **BLOQUEADO ANTES DEL FREEZE**.

Este documento asigna trabajo futuro. Su elaboración fue exclusivamente documental: se inspeccionaron Git, código, pruebas e informes existentes; no se conectó a AWS, ejecutó pruebas, preparó casos, creó FREEZE ni realizó inferencias. No se leyeron originales, requests o fichas individuales F4 para redactarlo. Las casillas pendientes no representan autorizaciones ni actividades realizadas.

**Responsabilidad de revisión designada:** Karol realizará personalmente y documentará la revisión humana de las 16 referencias antes de Fase 4 y la revisión semántica de las salidas necesaria para H2 después de las inferencias autorizadas. No se asigna esta tarea a otro integrante. Esta decisión organizativa no acredita independencia, aprobación de referencias ni autorización del FREEZE.

**Regla de evidencia para todas las etapas:** registrar fecha con zona horaria, responsable, SHA, entorno, comando real, código de salida, resultado, ubicación e integridad de los archivos. Separar evidencia histórica, verificación nueva, simulación e inferencia real. Toda aprobación debe identificar a una persona autorizada y el objeto/hash aprobado. Detenerse cuando falte una dependencia obligatoria; una decisión de alcance debe quedar aceptada y documentada, no asumida.

## 1. Objetivo y alcance del cierre

**Objetivo y resultado esperado:** entregar el MVP funcional, su evaluación científicamente defendible dentro del alcance alcanzado, documentación reproducible y versión final integrada en `develop`.

- [ ] Cerrar los bloqueos del modelo/controlador e infraestructura necesarios para el MVP.
- [ ] Cerrar el protocolo, realizar personalmente la revisión de referencias y salidas H2, y completar FREEZE, ejecución autorizada, recuperación y evaluación H1/H2.
- [ ] Validar aplicación, exportación y demostración; completar los entregables de la sección 21.
- [ ] Integrar finalmente `integration/final-validation` en `develop`, con revisiones, pruebas y SHA final.

**Dependencias:** permisos del repositorio, acceso autorizado a EC2 y responsables de aprobación científica/revisión. **Archivos base:** [README principal](../../README.md), [metodología](../methodology.md), este plan.

**Comprobación y evidencia:** matriz de tareas y decisiones P0/P1/P2. **Aceptación:** cada compromiso tiene prueba o tratamiento formal aceptado. **Detenerse:** si se pretende añadir funcionalidades, seleccionar otro modelo, rediseñar frontend, reescribir arquitectura o optimizar H1/H2 después de observar F4. Esas actividades quedan fuera del cierre.

## 2. Resumen ejecutivo del estado real

**Objetivo:** establecer una línea base comprobable antes de actuar.

| Elemento | Estado verificado al redactar | Alcance de la afirmación |
|---|---|---|
| HEAD local y rama publicada | `7fc29f86d50298207a2a480ac3989be175ec9cb1`, `integration/final-validation` | Consultados mediante Git y `ls-remote`; no se detectó un commit posterior publicado |
| Árbol de trabajo inicial | Limpio antes de crear este plan | El plan será un archivo nuevo pendiente de commit; no se registró automáticamente |
| `develop` local y publicado | `2c10019dccff0e261752f032ac156c8638ab7f65` | Es ancestro de integración; diferencia `develop...integration`: 0/2 commits, 29 archivos, 8324 inserciones y 66 eliminaciones |
| Último despliegue documentado | SHA `7fc29f86d50298207a2a480ac3989be175ec9cb1` | No se hizo una consulta nueva a EC2 en esta sesión |
| Ubuntu / preflight | 767 pruebas aprobadas en 11,92 s; preflight aprobado con observaciones | Evidencia histórica del nuevo SHA, con proveedor real bloqueado durante tests |
| Frontend | 141 pruebas y build aprobados | Evidencia local anterior; no prueba nueva ni demostración real B/C de esta sesión |
| Preparación F4 | Interrumpida por `proposal_context_budget_exceeded`: 1 request B y 0 C | Una preparación; no son inferencias ni resultados científicos |
| Referencias | 16 fichas provisionales, 14 determinadas y dos indeterminadas; revisión humana pendiente a cargo de Karol | Revisora designada; ninguna aprobación humana realizada o inferida por este plan |
| FREEZE y campaña | Ningún FREEZE definitivo ni ledger científico nuevo documentados | 0 llamadas reales F4 autorizadas, intentadas, exitosas y fallidas; 32 previstas sin autorizar |
| H1/H2 | Sin evaluar | No hay TP/FP/FN/F1 o tasas H2 reales que publicar |

- [ ] Revalidar esta tabla y localizar cualquier estado posterior antes de escribir sobre la rama o instancia.
- [ ] Tratar las cifras como observaciones fechadas, nunca como garantías actuales de capacidad o calidad.

**Fuentes y evidencia:** [informe de estado más reciente](evidencias-publicables/aws/INFORME_FINAL_ESTADO.PUBLICABLE.md), [log nativo](evidencias-publicables/pruebas/aws_native_tests.PUBLICABLE.txt), [recuperación verificada](evidencias-publicables/aws/LOCAL_RECOVERY_VERIFIED.json), [incidente conservado](evidencias-publicables/evaluacion/SITUACION_EXPERIMENTAL.PUBLICABLE.json).

**Dependencias:** acceso a esos archivos locales, que están ignorados por Git. **Aceptación:** línea base ratificada o reemplazada por evidencia posterior identificada. **Detenerse:** ante información contradictoria; no ejecutar de nuevo la preparación para averiguar el estado. Si los logs no acompañan otro clon, solicitar el paquete restringido y sus hashes, sin inventar ubicaciones o resultados.

## 3. Rama base `integration/final-validation`

**Objetivo y resultado esperado:** continuar sobre la rama integrada y mantener trazabilidad de cada corrección, sin merges parciales a `develop`.

- [ ] Comprobar rama, HEAD, árbol, commits publicados y diferencias con `develop`.
- [ ] Coordinar cambios concurrentes antes de actualizar o escribir la rama compartida.
- [ ] Trabajar directamente en `integration/final-validation`; no crear otra rama sin una necesidad acordada.
- [ ] Registrar cada corrección aprobada mediante un commit identificable y publicar esa rama.
- [ ] Mantener muestras, secretos, resultados protegidos y logs voluminosos fuera de nuevos commits.

Comandos de inspección comprobados; ejecutar desde la raíz:

```sh
git branch --show-current
git rev-parse HEAD
git --no-optional-locks status --porcelain=v1 --untracked-files=all
git ls-remote --exit-code origin refs/heads/integration/final-validation refs/heads/develop
git log --oneline develop..integration/final-validation
git diff --stat develop...integration/final-validation
git rev-list --left-right --count develop...integration/final-validation
```

Las referencias locales de `origin` pueden estar desactualizadas. Karol deberá actualizar referencias mediante `git fetch origin` cuando tenga permiso y haya coordinado la sesión; no confundir esa operación futura con la inspección de esta documentación. Si el árbol está sucio, identificar propietario y propósito de cada cambio antes de continuar; no borrarlo ni agregarlo indiscriminadamente.

**Dependencias:** sección 2 y permisos/coordinación. **Archivos:** [convenciones de desarrollo](../development.md), `.gitignore`, diff de la corrección. **Pruebas/evidencias:** estado antes/después, revisión, SHA completo y correspondencia publicada; `git diff --check` para los cambios. **Aceptación:** fuente limpia y publicada por SHA, cambios revisados y sin sobreescribir trabajo concurrente. **Detenerse:** ante divergencia, secretos, conflictos no comprendidos o falta de autorización de commit/push. No usar reset/clean/force-push para resolverlo.

## 4. Arquitectura y configuración definitiva

**Objetivo:** verificar el perfil real que se ejecuta, conservando la comparabilidad B/C.

| Componente | Configuración comprobada en el código actual |
|---|---|
| Aplicación | FastAPI/Python y React/TypeScript/Vite; aplicación 0.3.0; análisis estático sin ejecutar PowerShell |
| A | Recuperación 1A y detección 1B; sin proveedor LLM |
| B | Original con preprocesamiento común v2; sin recuperación adicional |
| C | Mismo modelo, parámetros, política y postprocesamiento; añade recuperación verificada 1A |
| Perfil | `PSI_LLM_PROFILE=qwen3coder-v2`; omitirlo conserva Qwen14 histórico; `.env` no se carga automáticamente |
| Modelo / digest | `qwen3-coder:30b` / `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca` |
| Estrategia | `v2-deterministic-layers-2` |
| Sanitizador / verificador | `comment-blanking-v2-diagnostics` / `evidence-check-v2-bounded` |
| Política v2 normalizada | SHA-256 `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081` |
| Proveedor | Ollama en `127.0.0.1:11434`; sin fallback o descarga automática |
| Inferencia | CPU `num_gpu=0`, temperatura 0, seed 42, contexto 8192, salida 2048, diez hilos; plazo absoluto 300 s, cero reintentos automáticos |
| Opciones adicionales heredadas | batch 256, repeat_penalty 1, presence/frequency_penalty 0, top_k 20, top_p 0,95, min_p 0, keep_alive 5m; sin `think` ni parámetro de generación especulativa en el request Qwen3 |
| Recursos | `linux-resident-mode-aware-v1`; recolector `linux-proc-cgroup-v2-v2`; binding `linux-model-filesystem-binding-v1` |

- [ ] Comprobar la cadena de perfil y herencia; no tomar el modelo base histórico de `pipelines/config.py` como modelo efectivo.
- [ ] Registrar settings y request exactos, no solo las variables de entorno.
- [ ] Probar con fixtures que C no recibe etiquetas 1B, predicciones B, referencias, respuestas previas o información de hipótesis.
- [ ] Separar opciones solicitadas de datos efectivamente observables: el API no devuelve todas las opciones de muestreo.

**Dependencias:** SHA revisado. **Archivos:** [selección del perfil](../../backend/app/api/application.py), [Qwen3](../../backend/app/services/llm/qwen3coder.py), [perfil web v2](../../backend/app/services/llm/qwen3coder_prototype.py), [opciones heredadas](../../backend/app/services/llm/qwen14.py), [estrategia](../../backend/app/services/pipelines/strategy.py), [sanitizador](../../backend/app/services/pipelines/sanitize.py), [verificador](../../backend/app/services/pipelines/evidence_check.py), [bindings experimentales](../../experiments/phase4/profile.py).

**Pruebas/evidencias:** contratos y payloads sintéticos de la sección 16; hash normalizado y hash de bytes de política. **Aceptación:** perfil y contrato idénticos entre B/C salvo recuperación. **Detenerse:** ante cualquier cambio no aprobado de modelo, política, estrategia, parámetros, timeout o postprocesamiento.

## 5. Infraestructura AWS

**Objetivo y resultado esperado:** disponer de una copia aislada y verificable, con recursos y almacenamiento observables sin alterar los servicios históricos.

Última captura conservada: **2026-11-09 21:07:02 −05:00**, equivalente a `2026-11-10T02:07:02.660323+00:00`. Ubuntu 26.04.1 LTS, kernel 7.0.0-1014-aws, x86_64, ocho vCPU, Python 3.13.18 en el venv, Ollama 0.40.15, RAM física 33.647.419.392 bytes, disponible 32.890.433.536 y disco libre 8.369.348.608 bytes. Sin swap; overcommit 0. Es información histórica, no disponibilidad reservada.

Rutas documentadas, con el HOME del usuario SSH abreviado como `~` para no publicar una ruta personal absoluta. Karol debe resolver y comprobar la ruta real en la instancia; no introducir `~` literalmente en un binding que exige rutas absolutas:

| Uso | Ruta remota |
|---|---|
| Copia validada | `~/powershell-insight-ai-final-7fc29f86d50298207a2a480ac3989be175ec9cb1` |
| Copia anterior | `~/powershell-insight-ai-final-18f772ecfbf2241616ad948f36318bcb6abc6e8d` |
| Repositorio / laboratorio históricos | `~/powershell-insight-ai` / `~/powershell-insight-ai-model-lab` |
| Almacén canónico registrado / ancestro de medición | `/usr/share/ollama/.ollama/models` / `/usr/share/ollama` |

- [ ] Conectar con `ssh psi-aws`; verificar identidad, versión, procesos, residentes, espacio, permisos y ausencia de campañas activas.
- [ ] Actualizar la IP del alias por el procedimiento autorizado si cambió; no leer ni compartir la clave privada.
- [ ] Desplegar cada nuevo SHA en otra copia identificable; conservar las copias anteriores y R1–R7.
- [ ] Transferir exclusivamente una lista revisada de fuentes de ese commit mediante `git archive` o checkout limpio. No archivar indiscriminadamente todo HEAD: existen históricos versionados.
- [ ] Separar fuentes, evidencia operativa del binding, datos científicos restringidos y build frontend; verificar sus procedencias y hashes por separado.
- [ ] Crear venv propio e instalar las dependencias fijadas por [requirements-app.txt](../../backend/requirements-app.txt) y [requirements-pilot.txt](../../backend/requirements-pilot.txt); no instalar globalmente ni descargar modelos.
- [ ] Estimar espacio para entorno, solicitudes, respuestas, monitorización y recuperación antes de instalar/copiar. No borrar históricos para conseguir capacidad.

Consultas sin generación usadas en la auditoría y aplicables a la futura comprobación remota:

```sh
id
uname -srmo
nproc
free -b
df -B1 "$HOME"
ss -ltn
ps -u ubuntu -o pid,ppid,comm,etime
curl --fail --silent --max-time 10 http://127.0.0.1:11434/api/version
curl --fail --silent --max-time 10 http://127.0.0.1:11434/api/tags
curl --fail --silent --max-time 10 http://127.0.0.1:11434/api/ps
```

**Preflight:** no existe subcomando CLI `preflight`. La ruta real es `native_state(settings, storage_binding=...)` y `Campaign.preflight(first=True)`. Reproducir un arnés aislado sin referencias F4, como el [sondeo nativo conservado](EVIDENCIAS.md#originales-no-publicados), solo después de verificar su hash, entradas, rutas de salida y que no despacha generación. Este arnés no es un CLI público versionado. No instanciar una propuesta F4 real como prueba de humo de infraestructura.

**Binding:** comprobar el SHA-256 del archivo real de evidencia, su procedencia, ruta canónica registrada, ancestro, montaje más específico, dispositivo, filesystem, capacidad y espacio actual. El código verifica formato del hash; la comprobación externa de que corresponde al archivo real sigue siendo obligatoria. `PSI_PHASE4_STORAGE_BINDING` incorpora el binding a la preparación. No sustituir `OLLAMA_MODELS` por una ruta ficticia. El ancestro no acredita lectura de los blobs ni resolución actual de descendientes protegidos.

**Dependencias/archivos:** [almacenamiento](../../experiments/phase4/storage.py), [recursos Linux](../../backend/app/services/pipelines/linux_resources.py), [política de admisión](../../backend/app/services/pipelines/resource_policy.py), [recursos del controlador](../../experiments/phase4/resources.py), [compatibilidad documentada](../ec2_linux_compatibility.md).

**Pruebas/evidencias:** pip check, preflight real sin generación, bindings inválidos con fixtures, hashes antes/después. Reserva fría vigente 23.968.709.120 bytes; caliente compatible 3 GiB; margen continuo 2 GiB; disco mínimo 2 GiB. En overcommit 0, commit es diagnóstico; en 2 también es vinculante; 1 se rechaza. No sumar swap como RAM ni exigir smaps cuando RSS/cgroups son observables.

**Aceptación:** preflight aprobado con observaciones explícitamente aceptadas, recursos actuales suficientes y fuentes iguales al artefacto identificado. **Detenerse:** si falta evidencia, hay montaje ambiguo, circuito bloqueado, otro modelo/campaña, poca capacidad o necesidad de privilegios nuevos. Sudo, permisos de Ollama, sysctl, swap, IAM, puertos y servicios ajenos requieren autorización específica; no modificarlos para forzar admisión.

## 6. Trabajo completado y comprobado

**Objetivo:** reutilizar evidencia válida sin confundirla con verificaciones posteriores.

| Evidencia heredada | Qué acredita | Qué no acredita |
|---|---|---|
| 767 tests nativos en `7fc29f8` | Backend, almacenamiento, rutas, contratos, Linux y fixtures de desarrollo de la selección registrada | Inferencia real exitosa, cobertura de toda suite científica o calidad H1/H2 |
| 141 tests frontend y build | Validación local anterior del frontend integrado | UI final desplegada en AWS ni nuevos resultados B/C reales |
| Preflight y archivo real del binding | Admisión y medición con evidencia vinculada en esa captura | Reserva de RAM, ausencia futura de OOM o lectura de pesos protegidos |
| Simulación del controlador | 48 registros/32 intenciones ficticias, checkpoints, duplicados y paradas | Autorización, ledger o campaña F4 reales |
| Recuperación local | Tres archivos de transferencia verificados, 40 archivos del paquete y cuatro de preparación parcial | Candidato completo apto para `seal` |
| Preservación | 2.765 hashes conocidos de históricos y despliegue anterior sin cambios, dentro del alcance registrado | Certificación de secretos, .git, venvs, cachés o symlinks excluidos |

- [ ] Contrastar los informes con sus logs/XML/recibos, SHA y fecha.
- [ ] Repetir solo verificaciones afectadas por cambios, fallos o incertidumbre actual; ejecutar la validación final integrada antes de cerrar.
- [ ] Corregir en la documentación nueva las referencias temporales obsoletas: `ec2_linux_compatibility.md` aún narra una corrección «pendiente de commit» que ya está publicada; README contiene una descripción genérica RAM/commit que no sustituye la política Linux efectiva.

**Dependencias y fuentes:** [integración local](../final_local_integration.md), [validación inicial](evidencias-publicables/aws/INFORME_VALIDACION_PROVISIONAL.18f772e.PUBLICABLE.md), [seguimiento de almacenamiento](EVIDENCIAS.md#originales-no-publicados), [estado posterior](evidencias-publicables/aws/INFORME_FINAL_ESTADO.PUBLICABLE.md).

**Prueba/evidencia:** tabla de vigencia por SHA en `INFORME_TECNICO.md`, sin sumar suites solapadas. **Aceptación:** cada afirmación distingue fecha, versión y alcance. **Detenerse:** si un informe anterior se presenta como aprobación vigente, inferencia o resultado independiente.

## 7. Inventario de bloqueos

**Objetivo y resultado esperado:** disponer de causas, decisiones y condiciones de salida verificables.

| ID | Bloqueo o brecha | Condición de salida |
|---|---|---|
| CTX-01 | `proposal_context_budget_exceeded` impide completar requests v2 | Diagnóstico independiente de F4, corrección/enmienda aprobada, regresión sintética, commit publicado y validación nativa; o impedimento formalmente aceptado |
| SCI-01 | Propuesta completa Qwen3 inexistente; la histórica usa Qwen14 | Protocolo Qwen3 aprobado y candidato íntegro con 32 requests/orden, sin sustituir históricos |
| HUM-01 | Revisión de las 16 referencias pendiente, asignada personalmente a Karol | Sus 16 fichas y acta nominativa con decisiones y hashes; limitación de independencia declarada y enmienda/alcance aprobado si lo exige el protocolo |
| SCI-02 | Fallos, denominadores, indeterminados y alcance de independencia sin aprobación final | Decisiones prospectivas aceptadas antes del FREEZE |
| FRZ-01 | Sin FREEZE ni autorización real nueva | Manifiesto completo, revisión y permisos explícitos; autorización ligada al congelado |
| EXP-01 | Sin campaña ni evaluación H1/H2 | Campaña autorizada y evaluada, o cierre formal de impedimento/alcance parcial sin resultados inventados |
| FUN-01 | Validación final real A/B/C y demo pendientes | Evidencia funcional actual, presupuesto real separado cuando proceda y guía reproducida |
| DOC-01 | Evidencias críticas en logs ignorados y cierre documental pendiente | Transferencia controlada, inventario accesible a Karol y documentos completos de la sección 21 |
| GIT-01 | Integración final a `develop` pendiente | Revisiones, merge completo, pruebas, publicación y SHA final documentado |

- [ ] Mantener estado, responsable de decisión, fecha, evidencia y dependencia de cada ID.
- [ ] Registrar nuevos problemas concretos sin ampliar el MVP; distinguir técnico, metodológico y operativo.

**Dependencias:** secciones 2 y 6. **Archivos/pruebas:** incidente de preparación, fuentes del controlador y recibos de validación; inspección, sin repetir F4 para diagnosticar. **Aceptación:** ningún bloqueo se cierra por una declaración sin prueba. **Detenerse:** si la solución cambia el contrato científico o exige actuar fuera de permisos.

## 8. Priorización P0/P1/P2

**Objetivo:** ordenar el trabajo por dependencias y evitar prolongar el alcance.

| Prioridad | Actividades | Regla de cierre |
|---|---|---|
| P0 | CTX-01, SCI-01/02, HUM-01, FRZ-01; integridad de fuentes, binding, recursos, autorización/ledger y preservación | Bloquean inferencias. Resolver o documentar una decisión formal de no ejecución; nunca eludir controles |
| P1 | EXP-01, FUN-01, DOC-01 y GIT-01; defectos funcionales comprometidos y reproducción final | Deben cerrarse antes de la entrega final o tener alcance formalmente aceptado |
| P2 | Mejoras no indispensables descubiertas durante el cierre | Registrar limitación/backlog y no ampliar implementación |

- [ ] Ejecutar primero diagnóstico seguro y decisión metodológica de contexto; organizar la entrega de evidencias y realizar Karol la revisión humana de referencias sin esperar nuevas inferencias.
- [ ] Continuar con candidato completo, aprobación, FREEZE y campaña solo al cerrar P0.
- [ ] Finalizar evaluación, validación, documentación, demo y merge; no iniciar selección de modelos, rediseño, mejoras cosméticas o rondas exploratorias innecesarias.

**Dependencias:** inventario de bloqueos. **Evidencia/prueba:** tablero de tareas con decisión y salida por ID; no requiere ejecutar modelos. **Aceptación:** todos los P0/P1 tienen criterio y responsable de aceptación. **Detenerse:** si se reclasifica un bloqueo como mejora para omitirlo.

## 9. Corrección del presupuesto de contexto

**Objetivo:** determinar la causa raíz y una solución mínima defendible sin calibrar sobre F4.

La regla de [prepare.py](../../experiments/phase4/prepare.py) compara `sum(len(message.content.encode())) + context_overhead_tokens + num_predict <= num_ctx`. Con los defaults vigentes: `bytes de messages + 512 + 2048 <= 8192`, por lo que quedan 5632 bytes de mensajes. La política normalizada ocupa 3241 bytes en la captura documentada. El adaptador [qwen14.py](../../backend/app/services/llm/qwen14.py), heredado por Qwen3, aplica la misma clase de cota `message-bytes-v2` antes de despachar. Es una guarda conservadora, no una medición real del tokenizer ni prueba de insuficiencia del modelo.

- [ ] Preservar el intento parcial, sus cuatro archivos y traceback; no volver a ejecutar prepare contra ese destino.
- [ ] Inspeccionar ambos cálculos y el payload final: política, serialización, preprocesamiento, recuperación, metadatos y reservas. Verificar que las reglas de preparación y despacho coincidan.
- [ ] Reproducir exclusivamente con fixtures de desarrollo: ASCII/Unicode, comentarios, recuperación vacía/multicapa, límites exactos y exceso de presupuesto, sin red real.
- [ ] Distinguir una protección deliberada de un defecto técnico. No declarar incorrecto el estimador solo porque rechaza F4.
- [ ] Evaluar una reserva independiente para la nueva preparación; registrar exposición previa y decisión sobre validez de la reserva actual. La preparación no observó respuestas del LLM, pero usar sus contenidos para ajustar la solución comprometería la independencia.
- [ ] Diseñar y revisar una corrección mínima. Si se propone otro método de contabilidad, justificar su mecanismo, límites y compatibilidad con la versión de Ollama/tokenización sin inventar una API disponible.
- [ ] Obtener aprobación técnica/metodológica antes de modificar un componente científico. Mantener modelo, contexto 8192, salida 2048 y demás parámetros salvo enmienda explícita; no truncar original, recuperación o evidencia silenciosamente.
- [ ] Implementar la solución aprobada en integración, añadir regresiones, verificar B/C equivalentes y ejecutar la selección segura.
- [ ] Registrar y publicar el nuevo commit con permiso; desplegar ese SHA en copia nueva y validar nativamente con fixtures no reservados.

**Dependencias:** Git coordinado, evidencia preservada y responsables de enmienda/independencia. **Archivos:** `prepare.py`, [context builder](../../backend/app/services/pipelines/context.py), `strategy.py`, `profile.py`, `qwen14.py`, pruebas de integración y v2 de la sección 16. **Comandos:** inspección Git de la sección 3 y regresiones de la 16; no existe un `prepare --dry-run` en el CLI actual.

**Evidencias a conservar:** causa raíz, alternativas, decisión de reserva, diff mínimo, aprobación, regresiones, SHA nuevo, manifiesto de despliegue y prueba nativa sin F4. **Aceptación:** solución justificada y común B/C, sin reducción silenciosa de entradas o controles; preparación científica futura únicamente tras aprobar su uso y el alcance de independencia. **Detenerse:** si para decidir la corrección se necesita inspeccionar/ajustar F4, cambiar parámetros para pasar o desconocer la enmienda. Si no hay solución compatible, documentar el impedimento y solicitar una decisión formal de alcance.

## 10. Cierre del protocolo Qwen3-Coder v2

**Objetivo y resultado esperado:** producir `PROTOCOLO_FASE4.md` prospectivo y completo, con decisiones trazables.

- [ ] Partir de [methodology.md](../methodology.md) y [protocolo histórico](../phase4_protocol_proposed.md), conservando H1: mejora del F1 C>B; H2: reducción de afirmaciones no respaldadas C<B.
- [ ] Identificar explícitamente qué se hereda, qué eligió/aprobó el responsable y qué sigue pendiente. La elección de modelo no aprueba calidad, referencias, protocolo final, FREEZE o generación.
- [ ] Registrar a Karol como revisora de referencias y salidas H2; declarar su participación previa en la preparación/evaluación y resolver mediante enmienda prospectiva aprobada cualquier requisito de independencia que no se satisfaga.
- [ ] Sustituir prospectivamente la especificación Qwen14 por Qwen3 v2 en el documento nuevo; conservar los documentos científicos anteriores sin sobrescribirlos.
- [ ] Fijar dataset, referencias, bloques, 8/8 estratos de recuperación, orden contrabalanceado, requests y límites; documentar cualquier enmienda antes de ver respuestas.
- [ ] Explicar la intervención de crudo original, postprocesamiento y predicción aceptada en H1/H2, según secciones 12 y 15.
- [ ] Confirmar que la reserva seleccionada sigue siendo apta; completar el audit de independencia y la revisión semántica. El intento actual falló antes de producir un audit nuevo satisfactorio.
- [ ] Aprobar criterios de fallo, datos faltantes, reanudación, autorización y cierre; no añadir análisis oportunistas tras obtener resultados.

**Dependencias:** CTX-01 y decisión de reserva; referencias humanas para aprobación final. **Archivos:** [métricas](../../experiments/phase4/metrics.py), [evaluación](../../experiments/phase4/evaluation.py), [protocolo del controlador](../../experiments/phase4/protocol.py), [borrador Qwen3 documental](evidencias-publicables/evaluacion/PROTOCOLO_QWEN3_PROVISIONAL.PUBLICABLE.md).

Interfaz actual comprobada por código; **no ejecutar estas operaciones ahora ni en el destino parcial**:

```sh
export PSI_LLM_PROFILE=qwen3coder-v2
export PYTHONPATH="$PWD/backend:$PWD"
export PSI_PHASE4_STORAGE_BINDING='/ruta/aprobada/binding.json'
.venv/bin/python -B -m experiments.phase4 --help
.venv/bin/python -B -m experiments.phase4 prepare
.venv/bin/python -B -m experiments.phase4 refresh-candidate
```

`/ruta/aprobada/binding.json` es un marcador que Karol debe sustituir por un archivo real verificado. `prepare` crea propuestas y lee F4: reservarlo para preparación científica autorizada tras la corrección, nunca como prueba de humo. `common.OUT` fija `artifacts/phase4_preparation` respecto de la raíz; no hay flag `--output`. Usar una copia nueva sin ese plan, o un mecanismo de versionado explícitamente revisado y aprobado. `refresh-candidate` solo actualiza una propuesta no congelada y preserva revisiones; no resuelve una preparación incompleta. `report-proposal` existe, pero `report.documents()` escribe `docs/phase4_references_proposed.md` y `docs/phase4_independence_review.md`: no ejecutarlo sobre documentos históricos para producir la nueva entrega.

**Pruebas/evidencia:** contratos y auditoría con fixtures antes de acceder a la reserva; después, integridad y consistencia del candidato científico sin usar resultados para retocar la implementación. **Aceptación:** protocolo nuevo, solicitudes y orden completos, enmiendas y aprobación identificadas. **Detenerse:** si falta un request, se mezclan perfiles/versiones o se intenta convertir el manifiesto parcial en candidato válido editando banderas.

## 11. Revisión humana de referencias

**Objetivo:** realizar Karol personalmente la revisión humana de las 16 referencias antes del FREEZE y documentar sus decisiones y limitaciones.

- [ ] Localizar el paquete restringido mediante [EVIDENCIAS.md](EVIDENCIAS.md#material-restringido), verificar hashes y confirmar el acceso autorizado de Karol; no publicar las fichas originales en las copias publicables.
- [ ] Inventariar F4-01 a F4-16: 14 determinadas y dos indeterminadas, sin publicar aquí originales, referencias o respuestas.
- [ ] Revisar personalmente los 16 scripts como texto, sin ejecutarlos, y contrastar las etiquetas esperadas B01–B07 con los comportamientos realmente respaldados.
- [ ] Verificar evidencias y citas de referencia, inclusiones/exclusiones, activación, recuperación, seguridad, novedad lógica y agrupación; identificar inconsistencias y documentar decisiones motivadas.
- [ ] Mantener `null` en referencias indeterminadas y respetar conocidos mínimos/alcance; no convertirlas en negativos completos para simplificar métricas.
- [ ] Completar las 16 fichas con nombre de Karol, rol y autorización, fecha con zona horaria, decisión, observaciones y exposición previa; distinguir revisión pendiente de revisión terminada.
- [ ] Resolver o documentar las discrepancias y registrar correcciones justificadas cuando procedan. Si cambian referencias/bloques, versionar el candidato y confirmar de nuevo sus hashes y revisión antes de sellar; no ajustar código con F4.
- [ ] Vincular el acta de Karol al hash del candidato científico definitivo y a los hashes de originales/referencias; registrar su resultado en los entregables de cierre.
- [ ] Declarar expresamente si Karol participó en construir las referencias. En ese caso, presentar su revisión como humana, sin calificarla como independiente.
- [ ] Si un protocolo vigente exige expresamente independencia de la persona revisora, identificar la cláusula y preparar una enmienda metodológica prospectiva o decisión formal de alcance para aprobación del responsable. No asignar por este plan otro revisor ni modificar silenciosamente controles para simular independencia.

**Dependencias:** decisión de reserva y candidato final completo. Puede adelantarse revisión documental, pero deberá ratificarse contra su identidad final. **Archivos:** [procedimiento histórico](../phase4_human_review.md), paquete y plantillas restringidas indexados en EVIDENCIAS.md. La asignación actual corresponde a Karol; las instrucciones históricas no constituyen una segunda asignación.

**Pruebas/evidencias:** 16 decisiones trazables de Karol, registro de discrepancias y acta; validación formal de `Proposal.seal`. La plantilla documental `reference_review.PROVISIONAL.template.json` no es compatible con seal ni acredita aprobación. La plantilla del candidato completo deberá conservar el esquema que exige `protocol.py`. La bandera `semantic_independence_approved` se refiere a la independencia semántica de los casos; no demuestra por sí misma independencia de la revisora.

**Aceptación:** revisión de las 16 referencias efectivamente realizada por Karol, nominativa y ligada al candidato; limitaciones declaradas y cualquier enmienda necesaria aprobada antes del FREEZE. **Detenerse:** si falta revisión, autoridad, correspondencia de hashes o decisión sobre un requisito metodológico vigente; no inventar firmas, segundo revisor, cegamiento, acuerdos o aprobaciones del equipo. La IA no es revisora humana y actualizar este plan no aprueba el FREEZE.

## 12. Política de fallos y denominadores

**Objetivo:** aprobar prospectivamente el tratamiento que aplicarán controlador, evaluador y revisión humana.

| Evento | Acción operativa antes fijada | H1/H2 y denominadores |
|---|---|---|
| `evidence_check_incoherent` terminal con estado íntegro | Conservar crudo y diagnóstico; no publicar predicción ni reintentar. El código lo trata como ordinario si pasan el resto de comprobaciones | Predicción `null`; positivos determinados como FN de cobertura y sin exactitud de conjunto. H2 revisa crudo si es adjudicable |
| JSON terminal inválido | Conservar bytes/diagnóstico, no pedir reparación al LLM | No utilizable para H1; H2 no recibe cero favorable por ser ilegible |
| Terminal `done_reason=length` | Registrar límite, raw, tiempos y tokens; distinguirlo de respuesta no terminal | Usabilidad según resultado del pipeline; conservar faltante y revisar solo lo que realmente existe |
| Timeout de 300 s/no terminal/HTTP crítico/recurso o estado incorrecto | Preservar intento, circuito y STOP según el controlador; detener despachos; nunca aumentar timeout ni repetir | Separar intentadas, fallidas y no evaluables. Campaña incompleta: descriptivos con cobertura, sin contraste completo H1/H2 |
| Fallo antes de reserva | Registrar causa y si hubo despacho | No inventar una llamada ni respuesta inexistente |
| Intención reservada sin resultado/estado incierto | Contabilizar como gastada y conciliar ledger/proceso/checkpoint | No repetir ni insertar una predicción negativa ficticia |
| Referencia indeterminada | Conservar ambos casos y sus diagnósticos | Fuera de métricas de etiquetas; dentro del inventario de 16, cobertura e incertidumbre/conocidos mínimos |

- [ ] Aprobar esta política y su correspondencia con `Campaign.hard_failure`, el adaptador y las métricas; no prometer que el controlador continúa después de cualquier timeout.
- [ ] Definir antes de la campaña las categorías utilizable, no utilizable, no ejecutada y no evaluable; conservarlas separadas.
- [ ] Fijar contadores: previstos, ejecutados A/B/C, autorizadas, reservadas, exitosas, timeouts, proveedor, rechazos, faltantes y cobertura humana.
- [ ] Probar con fixtures interrupción antes/después de reserva, respuesta parcial, pérdida de recursos, ledger huérfano y errores de almacenamiento.

**Dependencias:** protocolo y aprobación de denominadores. **Archivos:** `campaign.py`, [adaptador](../../backend/app/services/llm/qwen14.py), [serialización](../../backend/app/services/pipelines/serialization.py), `metrics.py`, `evaluation.py`.

**Pruebas/evidencia:** matriz evento→estado→consumo→métrica y regresiones sintéticas. En una campaña completa, clasificación principal sobre los 14 determinados; en una parcial, informar solo filas observadas con denominador explícito y pasos pendientes, sin rellenar no ejecutados. `predicted=null` no equivale a `[]`. **Aceptación:** no hay desapariciones silenciosas, doble conteo o métricas post hoc. **Detenerse:** ante un evento no cubierto que exija alterar el protocolo congelado.

## 13. FREEZE definitivo

**Objetivo y resultado esperado:** congelar un candidato completo, verificable y aprobado antes de cualquier inferencia F4.

- [ ] Confirmar SHA científico publicado, árbol limpio y bytes de todos los módulos efectivos/dependencias; incluir código del adaptador, controlador, storage, recursos y motores.
- [ ] Incluir Ubuntu, Python, Ollama, dependencias fijadas transitivas, modelo/digest, política normalizada y bytes, estrategia, sanitizador, verificador, opciones y límites.
- [ ] Vincular binding y archivo real de evidencia, hashes, métricas/denominadores, protocolo de fallos, referencias revisadas, dataset, 32 requests, orden y presupuesto.
- [ ] Revisar la cobertura de `refresh_candidate()`: el protocolo nuevo en `docs/cierre-modelo-fase4/PROTOCOLO_FASE4.md`, requisitos incluidos y demás dependencias reales no deben quedar fuera por confiar en globs antiguos. Resolver su inclusión prospectivamente antes de aprobar.
- [ ] Distinguir documentos inmutables de protocolo y archivos de resultados que se producirán después. No hacer que una actualización de resultados reescriba el protocolo congelado.
- [ ] Obtener aprobación expresa separada de protocolo, referencias, creación del FREEZE, máximo 32 llamadas y ejecución real. La autorización de infraestructura no las sustituye.
- [ ] Verificar el acta de revisión realizada por Karol, sus limitaciones y cualquier enmienda de independencia aprobada; sellar únicamente cuando coincidan todos los hashes y fechas y se satisfagan los controles vigentes.
- [ ] Crear después la autorización formal nueva ligada al FREEZE y al acta: declaración explícita del responsable, fecha, máximo exacto 32 y atestación de sesión exclusiva.

CLI comprobado, condicionado a los requisitos anteriores:

```sh
PYTHONPATH="$PWD/backend:$PWD" .venv/bin/python -B -m experiments.phase4 seal --personal-review /ruta/aprobada/revision.json
```

La ruta es un marcador. `seal` crea FREEZE pero no autoriza inferencias. No existe comando `authorize`: preparar el archivo formal según la plantilla del candidato completo y `Proposal.authorize`; verificar su aprobación real, no fabricar una declaración. El manifiesto candidato conserva el estado que exige el código (`approved_freeze=false`); el sellado se registra en `FREEZE.json`. No editar banderas manualmente ni reutilizar autorizaciones históricas/vencidas.

**Dependencias:** CTX-01, SCI-01/02 y HUM-01 cerrados, integridad técnica actual. **Archivos:** `common.py`, `prepare.py`, `protocol.py`; documentos finales y artefactos restringidos del candidato.

**Pruebas/evidencia:** inventario completo, actas, manifiesto, hash FREEZE y autorización; todo con ubicación duradera y permisos adecuados. **Aceptación:** candidato sin cambios pendientes, íntegro, revisado y autorizado, y plan de resultados/ledger independiente. **Detenerse:** si cambia SHA científico, componente, request, referencia, orden, timeout o protocolo: emitir un candidato nuevo y volver a aprobar, sin sobrescribir anteriores.

## 14. Ejecución de Fase 4

**Objetivo:** ejecutar una campaña autorizada sin duplicados, preservando cada intento y resultado, aunque la calidad sea desfavorable.

- [ ] Revalidar identidad EC2, versión/modelo/digest, capacidades, CPU/contexto, RAM/cgroups/disco, binding, circuitos y ausencia de otra campaña.
- [ ] Comprobar aprobación y correspondencia de autorización/FREEZE/acta/candidato; confirmar que no hay intenciones anteriores para esa campaña.
- [ ] Crear almacenamiento durable separado, con capacidad y permisos de escritura para ledger, requests, crudos, resultados, checkpoints, métricas y STOP.
- [ ] Revisar los 48 pasos del orden aprobado: 16 A y 32 LLM; contrabalanceo B/C previsto 8/8. No ejecutar primero todos B y luego todos C por comodidad.
- [ ] Preparar ejecución persistente que tolere desconexión SSH; comprobar disponibilidad y exclusión con fixtures antes de F4. Usar tmux/supervisor solo si existe y su procedimiento quedó validado; no asumir que está instalado.
- [ ] Iniciar un único controlador, monitorizar procesos, ledger, espacio, memoria y estados. No usar la API web o la demo en paralelo.
- [ ] Registrar inicio/fin, caso/modo/orden, modelo/digest, configuración, hashes, reserva previa, estado HTTP, crudo/bytes, tiempos/tokens, recursos, verificador y resultado.
- [ ] Ante desconexión, observar primero proceso, ledger, marker y checkpoints; no lanzar otra campaña. Ante incidente crítico, preservar y detener despachos conforme al protocolo.
- [ ] Cerrar con recuento real y estado completo/parcial/interrumpido; no confundir COMPLETED operativo con aprobación científica.

Interfaz comprobada contra `__main__.py` y el help conservado; solo después de autorización vigente:

```sh
PYTHONPATH="$PWD/backend:$PWD" .venv/bin/python -B -m experiments.phase4 run --authorization /ruta/aprobada/authorization.json
```

Reanudación exclusivamente tras conciliación y una autorización nueva que incluya `resume_explicitly_authorized=true` y el hash actual del ledger:

```sh
PYTHONPATH="$PWD/backend:$PWD" .venv/bin/python -B -m experiments.phase4 run --authorization /ruta/aprobada/resume-authorization.json --resume
```

`--resume` no omite un STOP crítico, checkpoint inválido o intención huérfana. No borrar STOP/marker/locks para continuar ni repetir una intención fallida o incierta. Una llamada reservada cuenta antes del envío de bytes. Si se requiere cambiar código o condiciones, detener y solicitar decisión sobre otro candidato; no presentar la versión alterada como el experimento congelado.

**Dependencias:** FREEZE y autorizaciones válidas; método persistente y exclusividad validados. **Archivos:** `campaign.py`, `protocol.py`, [gate/monitor](../../backend/app/services/pipelines/resources.py), [CampaignLock reutilizado](../../experiments/gemma4_v2/runner.py).

**Pruebas/evidencia:** ejecución persistente, locks y señales con fixtures antes de campaña; durante ella, registros reales íntegros. SIGINT puede registrar STOP; SIGTERM/SIGKILL o pérdida del proceso pueden dejar solo ledger/marker: comprobar siempre esos estados. **Aceptación:** 16 A y 32 intenciones terminales registradas sin duplicados, o cierre parcial/incidente formal con presupuesto y faltantes explícitos. **Detenerse:** ante recursos insuficientes, modelo incorrecto, circuito, integridad/almacenamiento fallidos, cambio contractual o autorización no válida. La calidad baja, FP/FN y rechazo ordinario no justifican ajustar el experimento.

## 15. Procesamiento y evaluación H1/H2

**Objetivo y resultado esperado:** producir `RESULTADOS_H1_H2.md` sustentado exclusivamente en datos reales y criterios congelados.

- [ ] Verificar primero identidades, hashes, ledger, resultados contiguos y checkpoints; conservar originales antes de derivar tablas.
- [ ] Separar crudo original del LLM, decisiones del verificador, predicción aceptada, fallos de postprocesamiento y no evaluables.
- [ ] Calcular TP/FP/FN, precisión, recall y F1 micro; macro sobre clases con soporte, métricas por clase, conjuntos exactos, cobertura A y diferencia pareada C−B conforme a `metrics.py`.
- [ ] Usar para H1 principal las predicciones publicadas por el pipeline; no promover etiquetas crudas descartadas. Presentar parejas ambas utilizables como secundarias con sesgo de selección explícito.
- [ ] Realizar Karol personalmente la revisión semántica H2 y el inventario completo y deduplicado de afirmaciones de todos los campos de cada salida cruda B/C, incluso rechazada, con citas, fuentes, razón, categoría y hash de salida.
- [ ] Comprobar si la evidencia respalda cada afirmación; registrar citas válidas, soporte insuficiente o contradictorio y sus decisiones, distinguiendo predicción original y etiqueta aceptada. No sustituir esta revisión por el verificador automático.
- [ ] Documentar en el informe científico la limitación si Karol participó tanto en preparar referencias/protocolo como en evaluar salidas; no declarar independencia, cegamiento o acuerdo entre revisores inexistentes.
- [ ] Calcular H2 según número de afirmaciones insuficientes/contradichas por unidad/bloque; fracción sin respaldo y apoyo permisivo como secundarios. Reportar literalidad de citas separada de soporte semántico.
- [ ] Mantener los dos indeterminados, sus conocidos mínimos e incertidumbre fuera solo de las métricas de etiquetas; publicar su tratamiento y cobertura.
- [ ] Reportar previstos, ejecutados, autorizadas/reservadas/exitosas, timeouts, fallos, rechazos, datos faltantes y revisiones completas; no rellenar salidas inexistentes.
- [ ] Interpretar por hipótesis: datos compatibles con apoyo, contradicción o insuficiencia para concluir; no asumir C>B ni declarar causalidad o generalización poblacional.

Comando de evaluación offline existente, con directorio real de revisiones personales hash-vinculadas:

```sh
PYTHONPATH="$PWD/backend:$PWD" .venv/bin/python -B -m experiments.phase4 evaluate --personal-reviews /ruta/aprobada/revisiones-salidas
```

`evaluate` sin revisiones no demuestra H2. `paired_H2` exige revisión completa y no concede una tasa favorable a inventarios vacíos/no adjudicables. La evaluación llama a `Campaign.existing()`: si hay una intención huérfana puede negarse a evaluar. Ese caso necesita conciliación e informe descriptivo de incidente sin modificar ledger ni fabricar resultados; prever su tratamiento antes de congelar.

**Dependencias:** evidencia recuperada, protocolo aprobado y revisión semántica posterior. **Archivos:** `metrics.py`, `evaluation.py`, `report.py`, actas y resultados congelados. **Pruebas/evidencia:** reproducir métricas con fixtures sintéticos antes del FREEZE; preservar JSON de evaluación y tablas derivadas. Mantener las sensibilidades previstas por bloques, bootstrap pareado 2000/seed 40716 y Holm solo si fueron aprobadas, con sus supuestos y limitaciones.

**Aceptación:** métricas reproducibles con denominadores visibles y conclusión proporcional al alcance; una campaña incompleta no se contrasta como completa. Si no hubo campaña, H1/H2 quedan no evaluadas y se documenta el impedimento, sin números ficticios. **Detenerse:** si el análisis exige alterar referencias, fórmulas o algoritmos después de observar F4.

## 16. Validación funcional y regresiones

**Objetivo:** comprobar el MVP final y las correcciones de cierre con datos de desarrollo, antes del FREEZE y nuevamente sobre la integración final cuando corresponda.

- [ ] Verificar instalación fijada, imports, FastAPI, perfil, contratos, A sin proveedor, B/C simulados, errores, recursos, locks y serialización/exportación.
- [ ] Probar evidencia retenida/descartada, Unicode, datos inválidos, límites, timeout simulado, interrupción y ausencia de reintentos.
- [ ] Usar temporales nuevos dentro de la copia de prueba y una guarda que impida conexiones al Ollama real durante la suite; no instalar dependencias solo para ocultar advertencias.
- [ ] Verificar frontend, integración HTTP/React, navegador, controles y exportación JSON; conservar salidas y procedencia del build.
- [ ] Validar B/C reales únicamente con autorización y presupuesto funcional separados, usando fixtures sintéticos, fuera de la campaña F4. Un clic en comparar implica dos análisis LLM.

Selección backend segura usada para las 767 pruebas de Ubuntu; el número puede cambiar tras una corrección aprobada. Desde la raíz de la copia aislada, con variables de temporal preparadas y la guarda de red validada:

```sh
export PYTHONPATH="$PWD/backend:$PWD"
.venv/bin/python -B -m pip check
.venv/bin/python -B -m pytest -p no:cacheprovider --basetemp "$psi_test_dir/work" --junitxml "$psi_test_dir/backend.xml" --tb=short -q \
  backend/tests/pipelines/test_phase4_storage.py \
  backend/tests/pipelines/test_linux_resources.py \
  backend/tests/pipelines/test_final_integration.py \
  backend/tests/pipelines/test_transport_resources.py \
  backend/tests/pipelines/test_qwen3coder_v2.py \
  backend/tests/pipelines/test_qwen3coder_regressions.py \
  backend/tests/pipelines/test_pipelines.py \
  backend/tests/api/test_api.py \
  backend/tests/deobfuscation backend/tests/behavior_detection
```

`psi_test_dir` debe apuntar a un directorio nuevo y exclusivo; fijar también TMPDIR dentro de la copia. No reutilizar temporales anteriores. Las pruebas API necesitan los fixtures frontend `comparison.json`, `partial.json` y `rejected.json`; su ausencia causó el primer fallo de empaquetado anterior y no debe corregirse inventando archivos.

Comandos frontend existentes en Windows, con dependencias del lock ya instaladas:

```powershell
npm.cmd --prefix frontend test -- --cache=false --fsModuleCache=false --configLoader=runner
npm.cmd --prefix frontend run build
npm.cmd --prefix frontend run test:integration -- --cache=false --fsModuleCache=false --configLoader=runner
```

La integración requiere su backend activo según el harness documentado. Para B/C simulados de navegador, seguir el servidor explícito `tests.api.integration_server:make_app` y [frontend/browser/integrated.mjs](../../frontend/browser/integrated.mjs), que exige `__test/state.synthetic=true`; no confundirlo con `app.main` o un proveedor real.

**Dependencias/archivos:** [guía de integración](../final_local_integration.md), [package.json](../../frontend/package.json), [contratos frontend](../../frontend/src/services/contracts.ts), [API](../../backend/app/api/application.py), selección anterior. **Evidencias:** XML/logs, versiones, errores, navegador y JSON exportado. No ejecutar genéricamente `pytest backend/tests`: la suite científica contiene lecturas reservadas y creación de propuestas/congelaciones.

**Aceptación:** funciones comprometidas verificadas y sin P0/P1 nuevos; cualquier llamada real tiene autorización e identidad separadas. **Detenerse:** si un test alcanza F4, abre proveedor real sin permiso, necesita modificar el contrato congelado o introduce rediseño/funcionalidad ajena al MVP.

## 17. Documentación en `docs/cierre-modelo-fase4/`

**Objetivo:** convertir esta carpeta en la fuente documental autosuficiente del cierre, con índices de evidencia restringida.

- [ ] Crear los entregables pendientes de la sección 21, distinguiendo estado técnico, experimental y científico.
- [ ] Mantener fechas, SHA, versiones, decisiones, límites y enlaces relativos válidos. Registrar evidencia nueva sin reescribir el significado de documentos históricos.
- [ ] En README.md del cierre, ordenar lectura, estados de aprobación, bloqueo/alcance y rutas de artefactos; actualizarlo al avanzar.
- [ ] En EVIDENCIAS.md, indexar identificadores, hashes, propietario/custodio, acceso, ubicación real y respaldo de material restringido, sin publicar su contenido.
- [ ] Conservar los originales de logs; publicar únicamente copias A aptas o derivados B revisados, con ambos hashes y procedencia, dentro de `evidencias-publicables/`. Mantener C fuera de Git y no eliminar D automáticamente.
- [ ] Verificar que los enlaces públicos funcionen desde un clon sin logs ignorados; usar EVIDENCIAS.md como índice de acceso controlado en vez de enlaces rotos a datos restringidos.
- [ ] Documentar qué documentos son parte inmutable del protocolo/FREEZE y cuáles son informes posteriores.
- [ ] Revisar diferencias y aprobación antes de commitear documentación; incluirla en integración y en el merge final.

**Dependencias:** evidencia de cada etapa. **Archivos:** los ocho entregables; esta actualización documental incluye plan, README, EVIDENCIAS y copias publicables revisadas. Los informes definitivos futuros continúan pendientes y no se rellenan con resultados ficticios. **Pruebas/evidencias:** revisión de enlaces, coherencia entre tablas/logs y secretos, estados sin aprobaciones ficticias. **Aceptación:** la carpeta explica qué se hizo, cómo repetirlo y dónde están las pruebas incluso si los logs ignorados no acompañan el clon. **Detenerse:** si un documento público exige copiar muestras, raw protegido, credenciales o archivos voluminosos; referenciar el almacenamiento adecuado.

## 18. Recuperación e integridad de evidencias

**Objetivo y resultado esperado:** obtener una copia local duradera, verificada y separada de los históricos, conservando originales remotos.

- [ ] Recuperar incluso si la campaña se bloquea: manifiesto, autorización, ledger, requests, crudos/bytes, resultados A/B/C, verificador, evidencia, métricas, errores, tiempos, hashes, evaluaciones y estado final.
- [ ] Inventariar tamaño/hash remoto antes de transferir; verificar SHA-256 local, cobertura de archivos y correspondencia caso/modo/orden/resultado/checkpoint.
- [ ] Mantener identificadores y originales de cada intento, incluidos fallidos, incompletos e inciertos; no limpiar evidencia para lograr una carpeta «completa».
- [ ] Confirmar duplicados=0, presupuesto real y que el código efectivo corresponde al FREEZE. Conservar sus bytes originales y procedencia de exportación.
- [ ] Preservar los paquetes parciales actuales antes de cualquier nuevo despliegue; no mezclar R1–R7, simulaciones, demo y F4.
- [ ] Registrar accesos, respaldos, retención y entrega a personas autorizadas; logs ignorados no constituyen por sí solos un mecanismo de distribución.

Comprobación de hashes disponible sin inferencias: `sha256sum` en Ubuntu y `Get-FileHash -Algorithm SHA256 -LiteralPath 'ARCHIVO_REAL'` en PowerShell. SSH/SCP fueron los métodos de transferencia comprobados; Karol deberá sustituir rutas por los destinos reales restringidos y verificar ambos extremos.

**Dependencias:** almacenamiento y acceso aprobados. **Archivos/evidencias de partida:** [recibo de exportación](evidencias-publicables/aws/final_export_receipt.json), [recibo parcial](EVIDENCIAS.md#material-restringido), [verificación local](evidencias-publicables/aws/LOCAL_RECOVERY_VERIFIED.json), [procedencia Git](evidencias-publicables/integracion/PROCEDENCIA_EXPORTACION_GIT.md).

En la exportación histórica de `7fc29f8`, 136/180 archivos cambiaron únicamente LF/CRLF por `core.autocrlf=true`; los bytes desplegados coinciden con los archivos transferidos, pero sus hashes pueden diferir de los blobs. Registrar ambos hashes, atributos y configuración de exportación. No normalizar retrospectivamente el FREEZE o los datos para hacer coincidir checksums.

**Pruebas/aceptación:** integridad completa de transferencias y manifiestos, trazabilidad de faltantes y acceso verificado al respaldo; fuente científica y SHA identificados sin ambigüedad. **Detenerse:** ante hash incorrecto, pérdida de originales, archivos fuera de inventario o posible duplicado. No borrar originales AWS ni históricos para resolverlo.

## 19. Guía de demostración

**Objetivo:** dejar `GUIA_DEMO.md` comprobada en el entorno final, sin usar F4 ni exponer Ollama.

- [ ] Documentar arranque de la instancia por el acceso AWS autorizado y consulta de su IP pública actual; no asumir que la IP histórica sigue vigente.
- [ ] Confirmar alias SSH, servicios/versiones/modelo/digest y recursos; no leer claves ni abrir puertos.
- [ ] Identificar SHA/build/venv y comprobar que frontend compilado corresponde a esa fuente. Preferir build local verificado a instalar Node en AWS solo para la demo.
- [ ] Iniciar backend en loopback con perfil explícito y frontend compilado servido por FastAPI, o usar el Vite local con proxy ya configurado.
- [ ] Comprobar health/capabilities/provider status; ejecutar un texto sintético de desarrollo en A sin ejecutar PowerShell.
- [ ] Con autorización funcional separada, demostrar B/C sobre datos sintéticos y registrar llamadas, estados, verificador y exportación JSON. No descontar demo del presupuesto F4 ni hacerla concurrente con el estudio.
- [ ] Ensayar errores de proveedor/recursos/contrato y explicar límites de la evidencia. Distinguir resultados en vivo, simulaciones y capturas guardadas.
- [ ] Documentar parada de los procesos de demo y del túnel. Detener EC2 solo con autorización y tras verificar que no hay campaña, transferencia o artefactos pendientes.

Arranque respaldado por el código, desde la raíz remota y con build previamente verificado:

```sh
export PSI_LLM_PROFILE=qwen3coder-v2
export PYTHONPATH="$PWD/backend:$PWD"
.venv/bin/python -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

Desde la máquina local, con puerto 8000 libre:

```sh
ssh -N -L 8000:127.0.0.1:8000 psi-aws
```

Abrir `http://127.0.0.1:8000` si existe `frontend/dist/index.html`; la API no publica automáticamente un frontend ausente. Consultar `/api/health`, `/api/capabilities` y `/api/provider/status` para comprobación sin generación. El túnel conecta al backend; el navegador no necesita acceso directo a 11434. Si se usa Vite local, su puerto 5173 y proxy `/api`→127.0.0.1:8000 están declarados en [vite.config.ts](../../frontend/vite.config.ts).

**Dependencias/archivos:** validación funcional, presupuesto de demo y permisos; `app.main`, `application.py`, build, configuración del proxy. **Pruebas/evidencias:** reproducción completa en otra sesión autorizada, versiones, capturas o acta, JSON exportado y errores ensayados, con datos sintéticos. **Aceptación:** guía reproducida, no solo propuesta, con procesos identificables y sin servicios públicos nuevos. **Detenerse:** si falta autorización B/C, se propone F4 como demo o se requiere cambiar el diseño frontend.

## 20. Merge a `develop`

**Objetivo y resultado esperado:** integrar una única versión final funcional, evaluada/documentada dentro del alcance aceptado, y publicar su SHA completo.

- [ ] Confirmar que todos los cambios de cierre están registrados y publicados en `integration/final-validation`, sin modificaciones concurrentes no coordinadas.
- [ ] Cerrar validación experimental y funcional, o disponer de acta explícita de impedimento/alcance parcial aceptado; no hacer un merge parcial para eludir P0/P1.
- [ ] Obtener revisión y autorización de integración según reglas y protección del repositorio; comparar con `develop` actualizado.
- [ ] Integrar toda la rama en `develop`, mediante PR o procedimiento autorizado. No sustituir la base por una nueva rama innecesaria.
- [ ] Resolver conflictos conservando las aportaciones válidas de todos los cambios; revisar cada resolución y no aceptar «ours/theirs» globalmente sin análisis.
- [ ] Repetir pruebas necesarias, build, contratos y comprobación funcional sobre el resultado integrado; revisar enlaces y ausencia de material restringido nuevo.
- [ ] Publicar `develop`, verificarlo en remoto y registrar SHA completo, revisión, conflictos/resolución y pruebas en `CIERRE_GIT.md`.
- [ ] Registrar por separado SHA científico congelado, SHA de integración y SHA final de develop. Un commit de documentación o merge posterior no cambia retroactivamente la versión que produjo los datos.
- [ ] Completar y publicar el acta de cierre Git, comprobar árbol limpio y ausencia de tareas P0/P1 sin decisión formal.

Comandos Git estándar para el procedimiento local **si** las reglas permiten merge directo y la estrategia fue aprobada; no ejecutarlos durante las etapas previas:

```sh
git fetch origin
git switch integration/final-validation
git status --short
git push origin integration/final-validation
git diff --stat origin/develop...integration/final-validation
git switch develop
git merge --ff-only origin/develop
git merge --no-ff integration/final-validation
# Resolver y registrar conflictos si existen; ejecutar las verificaciones finales antes de publicar.
git push origin develop
git rev-parse HEAD
git ls-remote --exit-code origin refs/heads/develop
```

Si el repositorio exige PR o estrategia distinta, seguir ese flujo y registrar el SHA efectivo resultante; no sortear protecciones. Si actualizar `CIERRE_GIT.md` después del merge genera otro commit documental, repetir la comprobación/publicación. Registrar el último SHA publicado en un recibo de cierre externo e inmutable, indexado desde `CIERRE_GIT.md`, además del SHA de merge registrado en el documento. No intentar incluir en un commit su propio SHA: evitar una cadena interminable de commits documentales y mantener trazables el SHA científico, el merge y el último HEAD publicado.

**Dependencias:** entregables, revisión y autorizaciones completas. **Archivos/evidencia:** diff completo, revisión/PR, pruebas finales, acta de alcance si corresponde y `CIERRE_GIT.md`. **Aceptación:** `develop` contiene código y documentación finales, pruebas aprobadas, SHA remoto coincidente y árbol limpio. **Detenerse:** ante revisión faltante, cambios concurrentes, conflicto no comprendido, pruebas fallidas o necesidad de operaciones destructivas.

## 21. Tabla de entregables

**Objetivo:** controlar la entrega documental y técnica sin presentar trabajo futuro como completado.

| Entregable en `docs/cierre-modelo-fase4/` | Contenido mínimo | Estado al redactar / aceptación |
|---|---|---|
| `README.md` | Índice, estado, orden de lectura, alcance, hashes clave y acceso a evidencia | Creado para esta etapa; mantenerlo actualizado al cerrar el trabajo pendiente |
| `PLAN_CIERRE_KAROL.md` | Este plan, prioridades, dependencias y checklist | Creado como documentación; requiere revisión/registro posterior autorizado |
| `INFORME_TECNICO.md` | Arquitectura, implementación definitiva, cambios, SHA, entorno/dependencias, AWS, recursos, despliegue, pruebas e incidencias | Pendiente; afirmaciones sustentadas y reproducibles |
| `PROTOCOLO_FASE4.md` | A/B/C, modelo/perfil, hipótesis, reserva/referencias, métricas/errores, orden, FREEZE, autorizaciones y enmiendas | Pendiente; prospectivo, revisado y vinculado al candidato final |
| `RESULTADOS_H1_H2.md` | Resultados reales, revisión semántica realizada por Karol, tablas/denominadores, crudo/aceptado, fallos, interpretación y límites de su participación | Pendiente; no crear cifras si no hubo campaña; documentar impedimento/alcance si se acepta |
| `EVIDENCIAS.md` | Inventario A/B/C/D, correspondencia original/copia, hashes, ubicaciones controladas de manifiestos, actas, ledger, requests/respuestas y respaldos | Creado con la selección documental actual; completar después con evidencia real del cierre |
| `GUIA_DEMO.md` | Arranque EC2, IP/SSH, servicios, túneles, A/B/C sintéticos autorizados, errores, exportación y parada | Pendiente; procedimiento reproducido en entorno final |
| `CIERRE_GIT.md` | Ramas, commits, revisiones, conflictos, pruebas, merge, publicación y SHA final de develop | Pendiente; correspondencia local/remoto y árbol limpio |

- [ ] Para cada entregable registrar responsable, versión, fecha, evidencia y aceptación.
- [ ] Mantener fuera de docs públicos originales F4, raw protegido, claves y archivos voluminosos; indexar su ubicación adecuada.
- [ ] Entregar también los artefactos técnicos restringidos necesarios para reproducción, con hashes y permisos, sin incorporarlos indiscriminadamente a Git.

**Dependencias:** etapas productoras. **Pruebas/evidencia:** revisión cruzada de todos los documentos y archivos accesibles. **Resultado esperado/aceptación:** conjunto autosuficiente para operación y evaluación dentro del alcance declarado. **Detenerse:** si faltan pruebas de un resultado o se propone rellenar un informe futuro con simulaciones no identificadas.

## 22. Riesgos y limitaciones

**Objetivo:** conservar explícitos los límites que condicionan aceptación e interpretación.

| Riesgo | Control / tratamiento exigido |
|---|---|
| Presupuesto de contexto bloqueado | Diagnóstico con desarrollo y enmienda aprobada; no eliminar guarda, truncar o ampliar parámetros para pasar F4 |
| Independencia/autoría/exposición | Acta de reserva y revisión humana; registrar cualquier compromiso de independencia y limitar conclusiones |
| Muestra pequeña y deliberada | Mantener emparejamiento/bloques; no afirmar representatividad, causalidad o significación poblacional |
| Literalidad confundida con verdad | Adjudicación semántica humana y separación de resultados crudos/aceptados; el verificador tiene alcance limitado |
| Falta de evaluación H2 | Karol realizará la revisión semántica; sin inventarios completos, marcar pendiente/no evaluable y no calcular éxito favorable |
| Misma persona en preparación y evaluación | Declarar el papel de Karol y su posible participación previa; no afirmar independencia inexistente; enmienda prospectiva o alcance formal si una obligación vigente lo exige |
| CPU/timeout y recursos | Diez hilos sobre ocho vCPU, plazo 300 s, monitor y reservas; reportar fallos sin ajustes post hoc |
| OOM/concurrencia | Admisión no reserva memoria; verificar sesión exclusiva y recursos en cada despacho, sin forzar kernel/swap |
| Almacén protegido | Binding/evidencia reales y montaje actual; registrar que descendientes/weights no se observan directamente |
| Cortes SSH/señales | Proceso persistente validado, ledger y checkpoints; incertidumbre consume intención, sin repetición |
| Procedencia de bytes | Hash de exportación y blob, LF/CRLF, versión/configuración de herramientas; no reescribir evidencia |
| Logs ignorados/no disponibles | Transferencia controlada y respaldo real; evidencias no garantizadas por clonar Git |
| Documentación histórica desfasada | Referencias temporales y especificación vigente en esta carpeta; no tratar antiguos resultados como validación nueva |
| Merge/documentación posterior | Mapeo de SHA científico y release; no atribuir a una versión nueva los resultados de otra |

- [ ] Evaluar cada riesgo, responsable y aceptación residual antes de las puertas afectadas.
- [ ] Registrar estimaciones como tales: 32×300 s son hasta 9600 s de plazos de generación, más A/preflights/I/O; no una cota total de campaña ni garantía de éxito.

**Dependencias/archivos:** protocolo, informes de recursos y actas. **Pruebas/evidencias:** regresiones sintéticas y observaciones reales fechadas, sin consumir F4 para medir un riesgo de desarrollo. **Aceptación:** limitaciones publicadas con alcance correcto. **Detenerse:** si para cerrarlas se requiere cambiar condiciones congeladas o esconder resultados negativos.

## 23. Checklist de aceptación

**Objetivo:** verificar la entrega completa con evidencia, no solo marcar tareas realizadas.

- [ ] Rama de integración correcta, cambios coordinados, commits revisados y publicados, sin secretos o resultados protegidos nuevos.
- [ ] CTX-01 resuelto con prueba independiente de F4 y validación nativa, o impedimento formal aceptado que impide inferencias.
- [ ] Prototipo final verificado: A sin proveedor, B/C simulados y reales cuando estén autorizados, errores, evidencia y exportación.
- [ ] Modelo/perfil/digest, política, sanitizador, verificador, parámetros y recursos preservados o enmienda explícita aprobada.
- [ ] Protocolo y denominadores prospectivos, reserva/independencia de casos decididas y las 16 fichas de revisión humana realizadas y documentadas por Karol, con limitaciones/enmiendas aceptadas cuando proceda.
- [ ] Si hubo inferencias: FREEZE y autorización anteriores al primer intento, ledger independiente, orden y presupuesto correctos, sin duplicados/reintentos.
- [ ] Si no se ejecutó o se interrumpió: acta del impedimento/incidente, faltantes y consumo real; no declarar H1/H2 evaluadas sin datos.
- [ ] Crudos, procesados, decisiones, tiempos y errores preservados; recuperación y respaldos verificados.
- [ ] H1/H2 interpretadas dentro del alcance real, con métricas/denominadores reproducibles o imposibilidad explícita de estimarlas.
- [ ] Revisión humana H2 realizada por Karol después de las inferencias autorizadas, con decisiones, hashes y limitación de su participación documentados; sin usarla para cambiar métricas después de observar resultados.
- [ ] Originales preservados, inventario A/B/C/D y hashes actualizados; solo copias aptas/depuradas en Git, sin C ni temporales D y con enlaces públicos funcionales.
- [ ] Ocho documentos completos, coherentes y con rutas válidas; material restringido indexado y accesible a autorizados.
- [ ] Demo sintética reproducida y presupuesto separado; EC2/servicios con estado final registrado y parada solo autorizada.
- [ ] Merge final aprobado y ejecutado, conflictos revisados, pruebas de develop correctas, publicación/SHA final documentados y árbol limpio.
- [ ] Cero tareas P0/P1 abiertas sin resolución o decisión formal de alcance.

**Dependencias:** evidencias de todas las etapas. **Pruebas/evidencia:** revisión de aceptación técnica/científica y de repositorio, con identidades y fechas. **Resultado/aceptación:** lista completa sustentada; los incumplimientos tienen tratamiento explícito aceptado. **Detenerse:** si falta una aprobación, un artefacto o una prueba necesaria; no convertir ausencia de evidencia en aceptación.

## 24. Criterio de cierre final

**Objetivo y resultado esperado:** emitir un cierre técnico, operativo y científico honesto, con `develop` listo para la entrega académica dentro del alcance aceptado.

- [ ] Confirmar que los bloqueos indispensables están resueltos o tienen tratamiento formal aceptado y documentado; no quedan P0/P1 sin decisión.
- [ ] Confirmar prototipo y guía de demostración comprobados, documentación/evidencias organizadas y acceso a respaldos verificado.
- [ ] Confirmar protocolo/aprobaciones, revisión de referencias y salidas H2 efectuada por Karol, y campaña autorizada ejecutada/evaluada; si existe un impedimento formal, declarar el trabajo no realizado y sus consecuencias científicas.
- [ ] Confirmar que cualquier resultado/conclusión procede de datos reales. Sin campaña no existen métricas H1/H2; un cierre operativo por impedimento no es validación de hipótesis.
- [ ] Confirmar integración final a develop, pruebas correspondientes aprobadas, publicación y SHA final documentados, con correspondencia al SHA científico cuando exista.
- [ ] Registrar el estado final de EC2 y procesos; solicitar apagado cuando proceda, sin hacerlo sin permiso.

**Dependencias y evidencia:** checklist anterior, actas de aceptación/alcance, `CIERRE_GIT.md`, informes, inventario y SHA publicado. **Comprobaciones finales:** Git de la sección 20, pruebas aplicables y revisión cruzada documental; no se exige rendimiento perfecto ni que C gane a B.

El acta debe usar el estado que realmente corresponda: listo para aprobación del FREEZE, bloqueado antes del FREEZE, campaña completa y evaluada, completa con limitaciones, parcial y evaluada o interrumpida por incidente. Si se acepta cerrar la entrega con un impedimento, conservar además el estado científico bloqueado/no evaluado; no renombrarlo como campaña completa.

**Aceptación final:** los diez criterios de entrega —bloqueos tratados, prototipo verificado, protocolo/aprobaciones, campaña o impedimento, evaluación válida en su alcance, documentación, demo, merge, pruebas/SHA de develop y P0/P1 resueltos o formalmente acotados— cuentan con evidencia y aceptación. **Detenerse:** si se pretende declarar finalizado con un merge pendiente, una revisión humana inventada, una autorización inexistente o resultados no medidos.

**Estado de partida de este plan: BLOQUEADO ANTES DEL FREEZE.** Karol deberá reemplazarlo en los documentos de cierre solo cuando la evidencia y las aprobaciones permitan el estado siguiente.
