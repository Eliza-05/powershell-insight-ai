> Copia publicable derivada de un informe historico. Rutas operativas redactadas y enlaces ajustados; no es una nueva validacion, acta humana o autorizacion. La responsabilidad vigente de Karol consta en el plan.

# Validación AWS y candidato PROVISIONAL — PowerShell Insight AI

Fecha local: 9 de noviembre de 2026, America/Bogota. Las capturas JSON conservan su fecha UTC.

**Veredicto: BLOQUEADA ANTES DEL FREEZE.** El backend se desplegó y pasó su validación nativa sin generación. El preflight completo del controlador todavía falla por la ruta/permisos del almacenamiento de modelos. La propuesta científica versionada corresponde al modelo anterior y no permite sellar esta versión. No se creó FREEZE, autorización ni ledger de campaña real.

## A. Despliegue

Copia nueva: `<COPIA_AISLADA>`. Usuario `ubuntu`; directorio creado con modo 0700. Entorno `.venv` propio con Python 3.13.18, derivado del intérprete ya instalado; el Python general del sistema es 3.14.4. No se instaló Node en AWS ni se sirvió el frontend remoto. La fase experimental usa backend y controlador; el frontend se construyó y verificó localmente.

La transferencia fue `git archive` del SHA confirmado, con lista explícita de archivos: 166 archivos iniciales y tres fixtures de contratos adicionales. No es una copia indiscriminada del árbol local ni un checkout completo. Incluye fixtures sintéticos y del piloto de desarrollo; excluye resultados, FREEZE históricos, `.env`, claves privadas, entornos, cachés y datos F4. `experiments/phase4/dataset.py` no se transfirió; solo se registra su hash del commit en el manifiesto provisional.

## B. Git e integridad

- Rama: `integration/final-validation`.
- SHA local/remoto: `18f772ecfbf2241616ad948f36318bcb6abc6e8d`. Coincidencia confirmada dos veces con `git ls-remote`.
- Árbol limpio al inicio y después de las pruebas. Sin commit, push, merge ni cambio de rama.
- Archivo inicial SHA-256: `a16cc24b86c7f0b0a9be1aa01f9a0fa9e2532f6657559849aa79a5436f6a2914`.
- Cada archivo transferido se comparó con el SHA-256 del contenido producido por `git archive`.
- El commit nuevo no añade rutas de históricos ni de datasets reservados. Los históricos ya versionados son antecedentes explícitos y no se transfirieron.
- No hay `.env`, `.pem`, `.key`, `.p12` o `.pfx` versionados por esos nombres. El escaneo del paquete no encontró patrones de claves privadas, tokens GitHub, AWS ni API Google. Es un control limitado al paquete; no certifica toda la historia Git ni los archivos privados excluidos.
- Las fuentes Python del paquete se pudieron analizar sintácticamente y no se encontraron marcadores de conflicto. `git diff --check` pasó.

## C. AWS observado

Ubuntu 26.04.1 LTS, x86_64, kernel 7.0.0-1014-aws, ocho vCPU, RAM física 33.647.419.392 bytes, sin swap, cgroup v2. Ollama 0.40.15 escucha exclusivamente en `127.0.0.1:11434`. El último `/api/ps` está vacío y no se observaron controladores experimentales concurrentes. Esto es una captura puntual, no una reserva exclusiva de la instancia.

Disco libre final en la raíz: 8,439,164,928 bytes (7.860 GiB). Se conservaron los repositorios históricos; no se descargó otro modelo, no se alteró Ollama, IAM, puertos, servicios, kernel ni permisos de su almacenamiento. No se usó sudo ni se apagó la instancia.

## D. Pruebas de esta validación

| Verificación | Resultado real |
|---|---|
| Backend local, selección segura | 744 aprobadas, 19,58 s |
| Frontend local | 141 aprobadas, 11,34 s |
| Build TypeScript/Vite local | Aprobado |
| Backend Ubuntu, primer intento | 741 aprobadas y 3 fallos de empaquetado |
| Backend Ubuntu, paquete completado | 744 aprobadas, 12,38 s |
| pip check local y Ubuntu | Sin requisitos rotos |
| CLI `phase4 --help` y `run --help` | Disponible; run exige `--authorization`, admite `--resume` |
| Importación del backend, perfil v2, HTTP y A nativo | Aprobados con fixture sintético |
| B/C, exportación, errores, recursos y locks | Pruebas sintéticas aprobadas |
| Controlador completo, transporte simulado | 48 registros y 32 intenciones simuladas; checkpoints y duplicados verificados |
| Timeout e interrupción tras reserva, simulados | Parada, preservación y rechazo de repetición; intención huérfana detectada |
| Autorización real sin FREEZE | Rechazada por la guarda del protocolo |
| `native_state` sin OLLAMA_MODELS | Falla: `<HOME_SERVIDOR>/.ollama/models` no existe |
| `native_state` con ruta habitual del servicio | Falla: permiso denegado en `<ALMACEN_MODELO>` |

Las 744 pruebas se ejecutaron con datos de desarrollo y temporales propios. Se excluyeron la suite de Fase 4 y las suites que abren referencias reservadas o crean FREEZE. Esta selección es distinta de las 803 pruebas históricas; no se suman las cifras ni se presentan esas 803 como una comprobación AWS.

Durante las pruebas Ubuntu se bloqueó toda conexión al puerto real 11434 mediante un audit hook Python. La auditoría específica del controlador anuló el transporte de red y usó una propuesta ficticia; el hash del FREEZE se simuló solo en memoria. No demuestra que las referencias o la autorización de una campaña real estén aprobadas. Su primer intento falló porque faltaba ese stub del hash; se conservó el fallo y se corrigió únicamente el arnés de auditoría.

La primera suite AWS reveló que el paquete omitía `comparison.json`, `partial.json` y `rejected.json`, utilizados por `test_api.py`. Se añadieron exactamente los blobs del mismo SHA, sin cambiar código, y se repitió la selección completa. Se preservan ambos registros. La advertencia existente de Starlette/httpx se mantiene; no se cambiaron dependencias para ocultarla.

## E. Estado del FREEZE y candidato

`CANDIDATE.PROVISIONAL.json` liga el SHA, hashes de fuentes, dependencias, ambiente, parámetros propuestos y hashes de la propuesta reservada sin abrirla para desarrollo. **No es el manifiesto completo aceptable por `Proposal`, no aprueba referencias y no se debe pasar a `seal` o `run`.**

La propuesta versionada en `artifacts/phase4_preparation` todavía especifica `qwen2.5-coder:14b`, carece del perfil/estrategia v2 y su manifiesto presenta diez hashes desactualizados respecto de HEAD. Su plantilla tiene 0/16 aprobaciones personales y las tres aceptaciones generales en false. No se sobrescribieron esos antecedentes. Hace falta preparar una propuesta nueva en una ubicación independiente, con solicitudes B/C v2 y revisión humana ligada a su hash, después de resolver el bloqueo técnico.

## F. Presupuesto real

| Concepto | Cantidad |
|---|---:|
| Llamadas nuevas propuestas | 32 |
| Autorizadas actualmente | 0 |
| Intentadas con un modelo real | 0 |
| Exitosas | 0 |
| Fallidas/timeouts reales | 0 |
| Restantes bajo autorización vigente | 0 |
| Propuestas todavía sin autorizar/consumir | 32 |

Las intenciones del arnés son exclusivamente sintéticas y no pertenecen a F4 ni al presupuesto real.

## G–I. Hipótesis, tablas y métricas

H1 y H2 siguen **sin evaluar**. No hay inferencias independientes ni resultados F4. TP, FP, FN, precisión, recall, F1, afirmaciones no respaldadas y tasas de citas son **no medidos**, no cero.

El protocolo existente define H1 como diferencia de micro-F1 C−B sobre los 14 determinables fijos, conservando los rechazos como fallos de cobertura. H2 compara el número de afirmaciones factuales no respaldadas por unidad/bloque en las respuestas crudas, mediante revisión personal completa, estricta y ligada al hash. No se sustituye la adjudicación semántica con literalidad automática.

El orden propuesto existente usa las semillas 40716 para unidades y 61407 para contrabalanceo: A precede B/C, ocho unidades B primero y ocho C primero. Debe regenerarse y verificarse su vínculo con los requests v2 en el nuevo candidato, sin adaptar nada a resultados. Las sensibilidades por bloques, bootstrap y Holm solo se usarán conforme al protocolo aprobado; no se añaden fórmulas nuevas.

## J. Recursos, errores y límites prospectivos

La política observada es `linux-resident-mode-aware-v1`; recolector `linux-proc-cgroup-v2-v2`. En el sondeo: MemAvailable limitado por cgroups 32,862,126,080 bytes, reserva fría completa 23,968,709,120 bytes, margen sobre reserva 8,893,416,960 bytes. Se verificaron seis ubicaciones de la jerarquía; no hubo límite finito vinculante. `overcommit_memory=0`: el compromiso es diagnóstico, sin crédito por swap. El VmRSS de Ollama fue 37.744.640 bytes; smaps/PSS/privada no disponibles por permisos se conservaron como ausentes, sin renombrar RSS.

**Admisión de recursos no equivale a inferencia exitosa, autorización ni garantía frente a OOM.** Las observaciones son no atómicas; otra carga puede consumir el margen. Se mantendrán reserva fría, reserva caliente de 3 GiB, margen continuo de 2 GiB y disco mínimo de 2 GiB. No se cambia sysctl o swap. Diez hilos sobre ocho vCPU quedan como configuración fijada y riesgo de latencia, sin reducirlos.

Configuración propuesta común B/C: `qwen3-coder:30b`, digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`, perfil `qwen3coder-v2`, CPU `num_gpu=0`, temperatura 0, semilla 42, contexto 8192, salida 2048, diez hilos, timeout 300 s, sin reintentos, keep_alive 5m. El manifiesto contiene todas las opciones adicionales exactas de la clase vigente. Son parámetros preparados/solicitados; sin generación no existe comprobación de su consumo efectivo por el modelo. El API no devuelve todas las opciones efectivas.

Estrategia `v2-deterministic-layers-2`, sanitizador `comment-blanking-v2-diagnostics`, verificador `evidence-check-v2-bounded`. Política normalizada: `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081`; bytes desplegados: `c17d5b11001eefdd76c5b77538a4265d93ea3fbe35e579cd08f3e7e2bb94949f`.

B y C comparten política, opciones, esquema y postprocesamiento. B lleva solo `original`; C añade `deterministic_recovery`. Las pruebas no encontraron canales de etiquetas 1B, predicciones B o referencias dentro del request sintético. Se conservan respuesta original, diagnóstico y decisiones del verificador.

Propuesta de errores, pendiente de aprobación expresa:

1. `evidence_check_incoherent`: conservar crudo/diagnóstico; predicción publicada null, sin reintento. Si la respuesta es terminal y el estado íntegro, es rechazo ordinario. En H1, positivos determinables no recuperados cuentan como FN de cobertura; nunca se gana exactitud por ausencia de salida. H2 conserva el crudo para revisión, sin asumir cero errores.
2. Timeout: mantener 300 s, consumir y conservar el intento; detener nuevos despachos cuando queda circuito o estado remoto incierto. No reintentar ni excluir el registro. En campaña parcial, solo descripción con denominadores observados; no contraste H1/H2 como campaña completa.
3. JSON terminal inválido o salida limitada terminal: preservar bytes/crudo y diagnósticos; no confundir null con conjunto vacío. El controlador distingue rechazo ordinario de respuesta no terminal, incoherencia de estado, recursos o error HTTP crítico. Si H2 no tiene inventario semántico evaluable, queda pendiente/no evaluable.
4. Dos referencias indeterminadas: conservar los 16 casos; excluir solo esas dos referencias de las métricas de etiquetas conforme al protocolo, informar incertidumbre/conocidos mínimos y cobertura; no reasignarlas tras ver resultados.
5. Revisión humana: referencias, seguridad e independencia requieren persona real y hash del candidato nuevo; H2 requiere posteriormente revisión por salida. No se inventaron aprobaciones ni revisores.

El controlador persiste intención antes de bytes de chat, fsync, resultado exclusivo y checkpoint; verifica orden, presupuesto y hashes. Hay lock de campaña y gate del adaptador. Timeout/interrupción dejan STOP/circuito; una intención huérfana no se repite. `--resume` exige autorización explícita vinculada al ledger y no permite ignorar STOP. SIGINT/KeyboardInterrupt entra en la captura BaseException; SIGTERM/SIGKILL o fallo físico pueden terminar sin STOP, por lo que hay que conciliar proceso, ledger y marcador antes de reanudar. No se ha iniciado proceso persistente real; su procedimiento debe revisarse al llegar a la autorización.

Los 32 plazos de generación suman hasta 9.600 s (160 minutos), más A, metadatos, admisiones y almacenamiento; no es cota del tiempo total de campaña ni promesa de completitud. El límite de respuesta del transporte es 2 MiB por llamada; 64 MiB para 32 cuerpos crudos máximos, con expansión base64, JSON duplicado, requests y muestreo de recursos adicionales. La evidencia no permite una cota dura de artefactos totales o consumo máximo de RAM sin inferir; debe mantenerse reserva de disco y monitorización.

## K. Históricos, artefactos y ledger

Se compararon antes/después los hashes de 1.645 archivos del repositorio histórico y 951 del laboratorio: **2.596 archivos sin cambios**, cero errores de lectura dentro del alcance. Se excluyeron claves/archivos privados, .git, entornos, cachés y symlinks; no se certifica contenido excluido. El repositorio histórico conserva SHA `723c6075ec9e97c2b1abd9d915d6f153f1965cb6` y árbol limpio.

No existe ledger nuevo real. Los ledgers de simulación están bajo `verification/controller_synthetic_02` y llevan IDs `SYNTHETIC-DEVELOPMENT`; no se reutilizarán. Ruta futura propuesta: `<COPIA_AISLADA>/artifacts/phase4_preparation/execution/ledger.jsonl`; resultados y checkpoints hermanos. Antes de usarla deberán existir candidato/revisión/FREEZE/autorización válidos, sin intentos previos y con sesión exclusiva constatada.

Se recuperaron logs, XML, inventario de dependencias, sondeo y auditoría a `logs/final_18f772e/`, fuera de temporales y excluidos de Git. Se conservan originales remotos. El inventario SHA-256 final permite verificar la transferencia de los archivos recuperados.

## L–N. Documentos, riesgos y decisión pendiente

Archivos principales: este informe, `CANDIDATE.PROVISIONAL.json`, `payload.PROVISIONAL.json`, `git_audit.json`, `historical_integrity.json`, `existing_proposal_metadata.json`, XML/logs locales y AWS, y el inventario SHA-256. Ninguno es FREEZE o autorización.

Bloqueos actuales: ruta de modelos no verificable desde el usuario del candidato; propuesta anterior 14B y manifiesto obsoleto; revisión humana nominativa y hash-vinculada pendiente; protocolo/32 inferencias no autorizados. Por ello **no se presenta todavía una puerta científica lista para aprobar**.

La petición de permiso pendiente es únicamente para dos lecturas de metadatos:

```text
sudo -n -u ollama realpath --existing -- <ALMACEN_MODELO>
sudo -n -u ollama stat --file-system --format='%T %S %b %f %a' -- <ALMACEN_MODELO>
```

Tu instrucción requiere autorización adicional para cualquier uso de sudo. No se ejecutaron estas operaciones. No leen pesos, cambian permisos ni generan. Solo ayudarían a establecer ubicación y filesystem; **no resolverían por sí solas el preflight sin privilegios**. Cualquier corrección posterior de código debe presentarse, probarse y recibir aprobación de commit/push antes de redesplegar un SHA nuevo. No se propondrá un valor de OLLAMA_MODELS ficticio para forzar admisión.

Una vez resuelto ese punto, corresponde preparar el candidato completo nuevo, revisar referencias y presentar las 20 comprobaciones de autorización del prompt. Solo entonces solicitar aprobación explícita del protocolo, FREEZE, 32 inferencias y ejecución F4. Esta preparación no concede ninguno de esos permisos.

## O. Integración y entrega académica

Mantener la rama sin merge a develop hasta tener SHA/candidato coherentes, revisión de referencias y resultado científico documentado, sea completo, parcial o no concluyente. La entrega actual puede incluir el prototipo y estas pruebas técnicas, declarando la evaluación F4 pendiente. No presentar resultados exploratorios previos como evidencia independiente de H1/H2. La EC2 está encendida e inactiva en cuanto a inferencias observadas; apagarla requiere autorización separada.
