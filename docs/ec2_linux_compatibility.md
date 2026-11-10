# Compatibilidad prospectiva con EC2 Ubuntu

## Seguimiento: almacenamiento del candidato AWS, pendiente de commit

La copia aislada del SHA `18f772ecfbf2241616ad948f36318bcb6abc6e8d` pasó 744
pruebas nativas sin generación, pero `phase4.campaign.native_state` falla al
medir el almacén: el HOME de ubuntu no contiene modelos y la ruta del servicio
no es accesible a ese usuario. Dos consultas de metadatos autorizadas como
`ollama` confirmaron la ruta canónica `/usr/share/ollama/.ollama/models` y un
filesystem de 32.092.319.744 bytes, con unos 7,86 GiB disponibles en esa captura.
No se leyeron pesos ni se cambiaron permisos. La opción `--existing` propuesta
inicialmente para realpath falló; la ayuda confirmó `--canonicalize-existing`,
con la que se completó la misma consulta de ruta.

Se prepara localmente `linux-model-filesystem-binding-v1`, exclusivamente para
contabilidad de disco del controlador. Sin binding explícito conserva la ruta
directa y el fallo por permisos; no busca un padre silenciosamente. La opción
`PSI_PHASE4_STORAGE_BINDING` permite incorporar los metadatos operativos al
`configuration.json` de una propuesta nueva, que luego queda cubierto por el
manifiesto y la revisión del candidato. La validación de ese binding precede
la importación de cualquier material reservado.

El binding fija ruta canónica observada, ancestro accesible para statvfs,
dispositivo, montaje, raíz y tipo de filesystem, capacidad total y hash de la
evidencia técnica. Cada captura verifica la ruta del ancestro sin symlinks,
su condición de directorio, el montaje más específico para ambas ubicaciones y
la capacidad. Rechaza montajes adicionales o ambiguos, raíces ocultas,
filesystem cambiado, campos incompletos y un OLLAMA_MODELS contradictorio.
La lectura fresca de espacio disponible mantiene el mismo mínimo de 2 GiB.
No se sustituyen ni alteran modelo/digest, RAM, opciones LLM o hipótesis.

Límite explícito: se comprueba en vivo el filesystem mediante su ancestro, no
se vuelven a resolver los descendientes protegidos ni se leen los blobs. La
ruta canónica procede de la captura autorizada; modificaciones concurrentes
de enlaces o del almacén protegido siguen siendo un riesgo externo que debe
constar en la revisión y atestación de sesión exclusiva. Este mecanismo no
concede permisos ni garantiza la integridad de los pesos por lectura local.

**Esta corrección aún no está registrada ni desplegada.** Antes de usarla:
revisión del diff y de sus límites, autorización para commit/push, nuevo SHA
limpio confirmado en el remoto, nuevo despliegue por SHA y pruebas nativas
pertinentes. El SHA anterior y sus resultados AWS se conservan. Tampoco se ha
regenerado la propuesta F4 antigua de Qwen14 ni se ha creado un FREEZE.

---

Fecha: 2026-11-09. Política **aprobada prospectivamente y activada solo en el código local**.
Despliegue, ejecución nativa Ubuntu, inferencias y FREEZE siguen sin autorización.

Trabajo local en `integration/final-validation`, sobre HEAD
`2c10019dccff0e261752f032ac156c8638ab7f65`. El recolector Linux y los
adaptadores de Fase 4 estaban presentes en el árbol de trabajo sin staging;
su presencia no significa que estuvieran registrados en HEAD. Se conservan
los cambios anteriores. No se ha desplegado esta revisión.

## Observaciones y correcciones

La auditoría AWS 0 comprobó Ubuntu 26.04.1, cgroup v2, 8 vCPU, unos 31,34 GiB
de RAM, sin swap y Ollama 0.40.15. El repositorio remoto seguía limpio en
`723c6075ec9e97c2b1abd9d915d6f153f1965cb6`, con el monitor anterior de Windows.

Una consulta SSH adicional de solo lectura confirmó el montaje cgroup2 completo
con raíz `/`, el controlador `memory` disponible, overcommit 0, ratio 50 y
overcommit_kbytes 0. La sesión y Ollama pertenecen a ramas distintas. Los
valores públicos de Ollama cambiaron respecto del diagnóstico anterior:
VmRSS 36684 kB, RssAnon 10204 kB, RssFile 26480 kB y VmSwap 0 kB. Son una
observación puntual, no una predicción del consumo con el modelo cargado.

### Cgroups

`linux-proc-cgroup-v2-v2` verifica el montaje en `/proc/self/mountinfo` y el
controlador de memoria. Solo permite omitir `memory.max` en la raíz completa
verificada; no interpreta un archivo ausente en un subgrupo como `max`.
Rechaza montajes de subárbol con ancestros ocultos, membresías ambiguas/v1,
errores de permisos, contadores inválidos y jerarquías incompletas.

Identifica el grupo propio y los de Ollama y sus descendientes visibles. Lee
cada ancestro una sola vez, con sus propietarios. `max` significa ilimitado;
un límite numérico, incluido cero, es finito. Para límites finitos calcula
`max(0, memory.max-memory.current)`. Toma el mínimo de los márgenes aplicables
y MemAvailable; no resta dos veces consumos ni suma grupos superpuestos.
Aplicar la reserva completa también al grupo del backend es conservador y
puede rechazar configuraciones con límites pequeños en esa rama.

La colección no mueve procesos, no reserva RAM ni modifica controles. Un
montaje o proceso no observable impide certificar sus límites críticos.

### Métricas de procesos sin privilegios

VmRSS se registra como `rss_bytes`, con su carácter aproximado. Los campos
RssAnon/RssFile/RssShmem/VmSwap se conservan cuando existen. Smaps es opcional:
`private_bytes` y `pss_bytes` solo aparecen si sus contadores reales están
disponibles; las banderas `private_unavailable` y `pss_unavailable` explicitan
su ausencia. RSS no se renombra como privada, PSS o working set de Windows.

El preflight Linux admite observabilidad mediante RSS, sin exigir privada.
La admisión se basa en márgenes de host/cgroups, no en sumar RSS de procesos.
El consumo del cgroup incluye descendientes y otras cargas, por lo que tampoco
se suma al RSS. La falta de RSS crítico, membresía o límites sigue bloqueando.
No hace falta sudo, otro usuario, ACL ni capacidades nuevas para esta ruta.

## Política de admisión aprobada y efectiva

El usuario aprobó expresamente su adopción local en la solicitud «Activación
controlada de la política de recursos Linux antes del despliegue EC2», de esta
fecha. Esa aprobación no autoriza desplegar ni consumir intents LLM.

`linux-resident-mode-aware-v1` es ahora la decisión Linux efectiva en
`resource_policy.resource_admission`. Sustituye la función de propuesta, sin
mantener implementaciones paralelas ni interruptores de entorno o HTTP.
Estado, adaptador, revalidación anterior al despacho, monitor continuo y
preflight experimental consumen la misma función. Windows conserva
`ram-and-commit-v1`, sus fuentes y sus umbrales; el piloto histórico no cambia.

| Criterio | Política Linux efectiva |
|---|---|
| RAM | MemAvailable limitado por cada grupo aplicable debe cubrir toda la reserva |
| Frío Qwen3-Coder | 23968709120 bytes, sin reducir pesos, KV, buffers ni margen |
| Caliente compatible | Reserva de crecimiento más margen existentes: 3 GiB |
| Swap | Se registra, pero no incrementa la RAM admisible |
| Overcommit 0 | CommitLimit/Committed_AS se registran como diagnóstico, sin equipararlos a RAM |
| Overcommit 2 | Además se exige margen real de commit para toda la reserva |
| Overcommit 1 | Rechazado por esta política conservadora |
| Información incompleta | Rechazo seguro |
| Incertidumbre | Observaciones no atómicas; estimaciones y concurrencia pueden cambiar el margen |

Con el fixture del diagnóstico anterior: commit disponible 15775051776 bytes
frente a 23968709120 requeridos. En modo 0 se admite si los márgenes físicos y
cgroup cubren la reserva completa; commit no es un veto independiente. En modo
2 esos mismos datos se rechazan por `commit_reserve`. La decisión guarda versión,
umbral, checks, causas, papel del commit y copia de las observaciones utilizadas.
No se confunde la admisión de recursos con éxito o autorización de inferencia.

Se comprueban también la versión del recolector, los contadores, la consistencia
de márgenes derivados, los procesos observables y la cadena completa de grupos
para cada propietario. Metadatos ausentes o contradictorios rechazan con
`resource_snapshot_unavailable` e identifican el campo inválido. Una señal Linux
sin recolector reconocido no puede caer a los criterios Windows. Smaps sigue
siendo opcional; RSS y límites críticos siguen siendo obligatorios.

MemAvailable estima capacidad para nuevas aplicaciones sin swap; no representa
RAM reservada. CommitLimit tampoco es RAM libre. En overcommit 0 el kernel
decide mediante heurística; en modo 2 aplica el límite de compromiso. Ninguna
decisión de este monitor garantiza ausencia de OOM. Cancelar HTTP tampoco
demuestra que haya terminado el procesamiento remoto: se conserva el circuito
persistente ante interrupciones. No se modifican sysctl, swap ni Ollama.

Fuentes primarias:

- [Kernel: contabilidad overcommit](https://www.kernel.org/doc/html/latest/mm/overcommit-accounting.html).
- [Kernel: cgroup v2 y memory.max](https://docs.kernel.org/admin-guide/cgroup-v2.html).
- [Kernel: proc, MemAvailable y contadores de procesos](https://docs.kernel.org/filesystems/proc.html).

## Reproducibilidad y límites

Se mantienen modelo/digest, política v2, estrategia `v2-deterministic-layers-2`,
verificador `evidence-check-v2-bounded`, sanitizador
`comment-blanking-v2-diagnostics`, CPU, temperatura 0, seed 42, contexto 8192,
salida 2048, diez hilos, timeout 300 s y ausencia de reintentos. La discrepancia
de ocho vCPU frente a diez hilos queda como observación, sin cambiar parámetros.

No se cambian contratos HTTP tipados ni frontend; se añaden diagnósticos dentro
de mapas operativos existentes. No hay dependencias nuevas. Las pruebas usan
Python 3.13.3 en Windows y archivos temporales con estructura Linux: prueban
decisiones y errores, no equivalen a ejecutar este código en Ubuntu 26.04.

Las pruebas nuevas del controlador llaman únicamente a preflight con metadatos
sintéticos y una propuesta mínima; no abren casos, no llaman a `run`, no sellan,
no crean FREEZE y no reservan intents. No ejecutar la suite completa de Fase 4:
algunas pruebas existentes leen referencias reservadas o generan congelaciones.

Antes de desplegar: revisar los cambios y obtener autorización de commit y
despliegue; preparar un commit definitivo limpio y una copia aislada por SHA.
La aprobación de política ya está registrada y no debe solicitarse de nuevo.
El manifiesto prospectivo debe incluir estos módulos y versiones;
el inventario de fuentes existente ya recorre `backend/app` y Fase 4. No se
refrescan manifiestos antiguos durante esta tarea.

En la copia futura comprobar instalación Python fijada, lectura real sin
privilegios, todos los procesos del runner, cgroups, locks, espacio y rutas de
resultados, sin generar. El preflight nativo también necesita una ruta de
almacenamiento del modelo verificable: su valor por defecto bajo el HOME de
ubuntu no acredita el almacén del servicio Ollama. No asumir acceso a los blobs
ni cambiar permisos para resolverlo. La carga real y el consumo máximo quedan
pendientes de autorización independiente.

El laboratorio histórico permanece separado. Se identificaron 58 pares R7;
no se utilizan para desarrollar esta política ni se realiza replay. Recuperar
su paquete completo y certificar sus hashes será otra etapa, sin alterar
resultados, autorizaciones o ledger históricos. Las 16 referencias reservadas
no se abren en este trabajo.

Una segunda captura remota confirmó cero errores al enumerar status públicos,
seis ubicaciones cgroup aplicables y denegación de smaps de Ollama. Se
reconstruyeron exclusivamente estos metadatos en un temporal local y se ejecutó
el recolector nuevo contra ellos, reproduciendo PermissionError mediante mock:

- MemAvailable: 32937652224 bytes.
- Margen de commit: 15775244288 bytes.
- VmRSS de Ollama: 37568512 bytes.
- La reproducción previa rechazaba por commit. La revisión actual, comprobada
  con fixtures equivalentes, admite recursos en modo 0 con la reserva completa.

Esta reproducción no envía código nuevo a EC2 ni certifica su ejecución nativa.

## Validación anterior a la activación

Ejecutar con el entorno existente, sin instalar paquetes y con un temporal nuevo:

```powershell
$psiCompatTemp = Join-Path $env:TEMP ('psi-linux-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp "$psiCompatTemp" --tb=short -q backend/tests/pipelines/test_linux_resources.py backend/tests/pipelines/test_final_integration.py
```

La selección ampliada de backend conserva la descrita en
`final_local_integration.md`, añade `test_linux_resources.py` y
`test_transport_resources.py`, y excluye campañas/congelaciones y referencias
reservadas. El informe de esta tarea registra los resultados efectivos.

Resultados obtenidos:

| Comprobación | Resultado |
|---|---|
| Backend ampliado | 778 aprobadas en 99,28 s |
| Selección final tras últimos ajustes, solapada con la anterior | 192 aprobadas en 12,73 s |
| Frontend | 141 aprobadas en 10,06 s |
| pip check | Sin requisitos rotos |
| memory_snapshot nativo Windows | Contadores enteros y ecuación de commit correctos |
| git diff --check | Sin errores de whitespace |

La única advertencia de pytest fue la deprecación existente de Starlette/httpx.
No se instala httpx2 ni se alteran dependencias para ocultarla.

Comando backend ampliado (mismo temporal aislado):

```powershell
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp "$psiCompatTemp" --tb=short -q backend/tests/pipelines/test_linux_resources.py backend/tests/pipelines/test_final_integration.py backend/tests/pipelines/test_transport_resources.py backend/tests/pipelines/test_qwen3coder_v2.py backend/tests/pipelines/test_qwen3coder_regressions.py backend/tests/pipelines/test_pipelines.py backend/tests/api/test_api.py backend/tests/api/test_qwen14_prototype.py backend/tests/pipelines/test_qwen14_exploratory.py backend/tests/pipelines/test_qwen14.py::test_transport_rejects_wrong_model_and_missing_authorization backend/tests/pipelines/test_gemma4_v2.py backend/tests/deobfuscation backend/tests/behavior_detection
```

Comando de selección final: mismo comando pytest con los primeros cinco paths
de la selección ampliada, utilizando otro temporal nuevo.

```powershell
npm.cmd --prefix frontend test -- --cache=false --fsModuleCache=false --configLoader=runner
.\.venv\Scripts\python.exe -B -m pip check
git --no-optional-locks diff --check
```

Respecto de los 23 archivos inicialmente modificados/nuevos, se ampliaron seis:
`linux_resources.py`, `pipelines/resources.py`, `test_final_integration.py`,
`final_local_integration.md`, `phase4/campaign.py` y `phase4/resources.py`.
Los otros 17 conservan exactamente sus hashes iniciales. Se añadieron al
conjunto de cambios `llm/qwen14.py`, `resource_policy.py`,
`test_linux_resources.py` y este documento: 27 archivos sin staging, HEAD y rama
sin cambios. No se escribió en índices, autorizaciones o artefactos científicos.

## Activación local autorizada: evidencia de la revisión final

La adopción local sustituye la propuesta y la comparación dual anteriores. No
se cambió el recolector cgroup v2, los contratos HTTP, el contenido de requests,
el modelo/digest, política v2, estrategia, sanitizador, verificador o taxonomía.
Tampoco se cambia la reserva de 23968709120 bytes, los diez hilos ni los 300 s.

La decisión efectiva tiene una única entrada: `resource_admission(snapshot,
required_bytes)`. Su registro permite reconstruir reglas y resultado:

- `policy=linux-resident-mode-aware-v1`, reserva y observaciones copiadas.
- `allowed`, `checks`, `reasons` e `invalid_fields`.
- `overcommit_memory`, `commit_role` y `swap_credit_bytes=0`.
- Contadores de RAM, commit y swap, grupos con propietarios y RSS por proceso.
- `decision_scope=resources_only; not execution authorization`.

En modo 0 el check de commit es `null` (no aplicable como veto); en modo 2 es
booleano y vinculante. El modo 1 falla `supported_overcommit`. RAM o grupos
insuficientes fallan sus checks; datos incompletos/contradictorios fallan
`critical_accounting` con `resource_snapshot_unavailable`. El límite inferior
de commit no se sustituye por un número ficticio de RAM disponible.

La ruta Windows mantiene el identificador y criterios `ram-and-commit-v1`.
Qwen14 y Qwen3 comparten la decisión de recursos sin cambiar sus modelos,
mensajes ni validadores. Las pruebas comparan el request completo con el builder
del perfil y verifican la persistencia JSON UTF-8 sin pérdida de metadatos.

Pruebas realizadas en Windows/Python 3.13.3, con temporales nuevos:

| Comprobación de activación | Resultado |
|---|---|
| Linux y preparación sintética enfocadas | 87 aprobadas |
| Backend ampliado, selección documentada arriba | 803 aprobadas en 99,65 s |
| Última comprobación del archivo Linux tras reforzar smaps denegado | 73 aprobadas en 2,61 s |
| Frontend | 141 aprobadas en 12,64 s |
| Build | `tsc -b` y Vite correctos |
| pip check | Sin requisitos rotos |
| Medición nativa Windows y selección de política | Correctas |

Las selecciones se solapan. Los tests de frontend usan el mismo comando seguro
documentado arriba; el build se ejecutó con `npm.cmd --prefix frontend run build`.
La única advertencia pytest continúa siendo la deprecación existente
Starlette/httpx; no se instalaron paquetes. Las regresiones cubren modos 0/1/2,
raíces sin control de memoria, límites y ramas separadas, smaps denegado,
contabilidad ambigua, proveedor caído, modelo/digest incorrectos, timeout,
circuito bloqueado y recuperación simulada con operador explícito. No hay
reintentos automáticos. La app inicia con `PSI_LLM_PROFILE=qwen3coder-v2` y A
funciona sin consultar proveedor o memoria. HTTP B/C se prueba solo con mocks.

En esta activación no se hicieron nuevas consultas SSH: las características
EC2 proceden de las capturas previas y se prueban como fixtures, sin asumir
que los valores remotos actuales sigan siendo idénticos. No se copió ni ejecutó
código nuevo en AWS. **La ejecución nativa Ubuntu sigue sin verificarse.**

## Propuesta experimental que aún necesita aprobación científica

La autorización de recursos no aprueba una campaña ni sustituye la revisión
metodológica anterior al FREEZE. La inspección del controlador y métricas
mantiene esta propuesta prospectiva:

1. `evidence_check_incoherent` conserva respuesta y diagnóstico; es fallo de
   publicación ordinario si existe respuesta terminal válida. No se reintenta
   ni se elimina del denominador. Una interrupción de recursos/transporte sigue
   siendo un stop crítico, aunque coincida con otro error.
2. Timeout individual de 300 s y cero reintentos automáticos. Antes de salir
   cualquier request, el callback verifica payload/orden, presupuesto y gate,
   y persiste la reserva con flush/fsync. Un fallo no devuelve ese presupuesto.
3. El resultado y checkpoint se guardan antes de evaluar el stop. Los intents
   huérfanos no se vuelven a enviar; reanudación exige autorización expresa
   ligada al ledger y comprobaciones de continuidad e identidad.
4. H1 conserva todas las unidades determinables intentadas: una salida no
   utilizable no obtiene acierto exacto y genera FN para etiquetas positivas.
   Las referencias indeterminadas se informan por separado, según el diseño.
5. H2 conserva las salidas crudas, incluidas las rechazadas, y exige revisión
   humana completa vinculada por hashes. Una respuesta truncada o una campaña
   interrumpida no se convierte automáticamente en evidencia favorable ni
   en una evaluación completa. La adjudicación de respuestas parciales y la
   interpretación de una campaña incompleta deben aprobarse antes del FREEZE.

Estos puntos son coherentes con la implementación inspeccionada y las pruebas
sintéticas de fallo/denominadores; H1/H2, fórmulas, taxonomía, referencias y
resultados históricos permanecen sin cambios. El método y sus reglas deben
recibir aprobación científica explícita, junto con la revisión humana reservada.

## Procedimiento preparado para la siguiente autorización

No ejecutar estos pasos como parte de esta activación local:

1. Revisar el diff completo de `integration/final-validation`, incluyendo los
   27 archivos ya pendientes; confirmar fuentes, pruebas y hashes fijados.
2. Tras autorización de operaciones Git, registrar el código definitivo en un
   commit limpio. Identificar su SHA completo y el manifiesto del paquete.
3. Con autorización de despliegue, transferir exactamente esa revisión a
   `/home/ubuntu/powershell-insight-ai-final-<SHA>`, una carpeta nueva. No usar
   pull/checkout sobre el repositorio antiguo ni copiar sobre el laboratorio.
   Excluir claves, .env, entornos locales y artefactos históricos del paquete.
4. Crear un entorno Python aislado y fijado para la nueva copia. Usar el modelo
   y servicio Ollama existentes, sin duplicar pesos. Para el frontend, construir
   desde ese SHA con el lockfile y registrar hashes de los assets derivados;
   Node no estaba disponible en el PATH de EC2 durante la auditoría anterior.
5. Verificar de nuevo Ubuntu, Python, dependencias, modelo/digest, política,
   opciones, versión efectiva de recursos y cgroups de aplicación/Ollama. No
   asumir que las cifras históricas de RAM, disco o permisos siguen vigentes.
6. Ejecutar pruebas de recursos y API sin generación, usando fixtures y
   endpoints de metadatos. Comprobar locks/exclusividad en un temporal nuevo,
   disco y una ruta de almacenamiento del modelo verificable sin leer pesos.
   No limpiar circuitos de otras instalaciones ni modificar sysctl/servicios.
7. Asignar resultados, ledger, autorizaciones y checkpoints nuevos en la copia
   aislada. Mantener el laboratorio R1-R7 y sus hashes completamente separados.
8. Solo después de aprobar el entorno nativo: preparar el candidato definitivo,
   completar las aprobaciones científicas y humanas, verificar integridad de las
   16 referencias por el procedimiento autorizado y preparar el FREEZE. Las
   32 llamadas requieren autorización de ejecución independiente y vinculada.

El control de recursos ya está aprobado para esta implementación local. Las
autorizaciones pendientes corresponden al commit/despliegue y al experimento;
no se solicita de nuevo la decisión de memoria adoptada.

Veredicto local: **LISTO PARA REVISIÓN Y COMMIT**. Continúan 27 archivos sin
staging, en la misma rama y HEAD. En esta activación solo se ampliaron cinco
archivos ya pendientes: `resource_policy.py`, `llm/qwen14.py`,
`test_linux_resources.py`, este documento y `final_local_integration.md`.
Los otros 22 conservan sus hashes iniciales. También se verificaron intactos
modelo/perfil Qwen3, política v2, configuración, estrategia, sanitizador,
verificador y contratos. No se ejecutó ninguna operación Git de escritura.
