# Gemma 4 12B — evaluación limitada de viabilidad local

Fecha: **3 de noviembre de 2026, America/Bogota**.

**Decisión: BLOQUEADO OPERATIVAMENTE en el estado observado del equipo.** El runtime
instalado es compatible por versión, pero la RAM disponible no cubre una carga
conservadora con contexto y buffers más el margen de seguridad. Se aplicó la
instrucción de detenerse antes de descargar/cargar si el entorno no es seguro:
**cero descargas de pesos, cero intentos de inferencia de ocho autorizados**.
La calidad de Gemma y su capacidad real en C quedan **sin evaluar**.

## 1. Compatibilidad del modelo

Se consultó el registro oficial, sin enviar muestras, prompts, credenciales ni
datos del proyecto. Se conservaron únicamente metadatos públicos pequeños.

| Propiedad | Resultado verificable |
|---|---|
| Identificador autorizado | `gemma4:12b`, `library/gemma4`, tag local; ningún tag cloud |
| Runner/formato | `llamacpp` / GGUF |
| Parámetros declarados | 11,9B |
| Cuantización declarada | `Q4_K_M` en la configuración del manifiesto |
| Runtime mínimo del artefacto concreto | `requires=0.30.9` |
| CLI y servidor instalados | `0.40.13`, coincidentes; no requieren actualización por versión |
| Licencia | Apache 2.0; capa de licencia y SHA-256 verificados |
| Capacidades anunciadas | Texto/imagen, herramientas y pensamiento; no se habilitarían herramientas |
| Capacidades efectivas locales | No verificadas mediante `/api/show` o inferencia: modelo no instalado |
| Ventana anunciada | 256K; no se pretende asignarla completa |

El [catálogo oficial](https://ollama.com/library/gemma4:12b) describe las capacidades;
la [versión 0.30.3](https://github.com/ollama/ollama/releases/tag/v0.30.3) incorporó
soporte inicial para 12B. El requisito **0.30.9 del manifiesto actual** prevalece
sobre esa fecha de introducción. Esto acredita compatibilidad declarada por versión,
no una generación estructurada efectiva en este equipo.

La página del catálogo presenta varios backends y puede mostrar distintos IDs.
Para Windows se fijó la respuesta real del registro `llamacpp`, no un ID de MLX:

```text
GET https://registry.ollama.ai/v2/library/gemma4/manifests/12b
SHA-256 de los 1299 bytes exactos del manifiesto:
6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b
```

El servidor no devolvió `Docker-Content-Digest`; el digest anterior se calculó sobre
el cuerpo recibido. Es un **digest del manifiesto remoto**, no una comprobación de
pesos descargados. Se verificaron contra el manifiesto las capas pequeñas de
configuración, licencia y parámetros. Los pesos no se solicitaron.

Evidencia: [manifiesto exacto](../artifacts/local_model_gemma4_viability/registry_manifest.json),
[configuración](../artifacts/local_model_gemma4_viability/registry_config.txt),
[licencia](../artifacts/local_model_gemma4_viability/registry_license.txt) y
[recibo de consultas públicas](../artifacts/local_model_gemma4_viability/public_metadata_receipt.json).

## 2. Recursos reales y puerta de seguridad

Observación conservada: **13:39:13 de Bogotá / 18:39:13 UTC**.
Los valores cambian con otras aplicaciones; no son una reserva de memoria.

| Recurso | Bytes | GiB |
|---|---:|---:|
| RAM física utilizable total | 33.413.771.264 | 31,119 |
| RAM disponible | 11.619.966.976 | **10,822** |
| Límite de compromiso | 51.667.382.272 | 48,119 |
| Compromiso usado | 26.288.852.992 | 24,483 |
| Compromiso disponible | 25.378.529.280 | **23,636** |
| Espacio libre en volumen de modelos | 558.247.321.600 | 519,908 |

El directorio vigente `OLLAMA_MODELS` está fuera del repositorio, en el volumen C:;
su ruta exacta está en [preflight.json](../artifacts/local_model_gemma4_viability/preflight.json).
El almacenamiento permite los aproximadamente 8,02 GB del paquete y una reserva
adicional de 2 GiB. **El espacio y el compromiso no son el cuello de botella actual.**

CIM denegó lectura. Se usaron `GlobalMemoryStatusEx`, `Toolhelp32Snapshot` y
`shutil.disk_usage`, sin modificar Windows. `/api/ps` devolvió `models=[]`;
el inventario encontró el servicio y la aplicación Ollama, sin runner llama ni
otro Python salvo el colector. No se observó inferencia concurrente. Es una
comprobación puntual: no excluye futuros clientes externos ni adquiere exclusividad
global. El marcador de circuito estaba ausente y no se limpió ningún bloqueo.

Estimación previa a la carga, con **8192 tokens de contexto**, CPU y caché FP16:

| Componente | Bytes | GiB |
|---|---:|---:|
| Modelo principal | 7.381.383.680 | 6,874 |
| Proyector | 175.115.616 | 0,163 |
| Draft incluido en el tag | 465.109.152 | 0,433 |
| Total de capas tensoriales | 8.021.608.448 | **7,471** |
| Reserva KV conservadora | 2.818.572.288 | **2,625** |
| Reserva de buffers/carga/gramática/runtime | 2.147.483.648 | **2,000** |
| Margen libre de seguridad | 2.147.483.648 | **2,000** |
| **Disponible exigido antes de cargar** | **15.135.148.032** | **14,096** |

La [configuración publicada por Google](https://huggingface.co/google/gemma-4-12B-it/blob/main/config.json)
declara 48 capas: 40 sliding y 8 globales; respectivamente 8 cabezas KV × dimensión
256 y 1 cabeza KV × dimensión 512. La cota se calcula como
`2(K,V) × 2(bytes FP16) × 8192 × (40×8×256 + 8×1×512)`.
No supone que el runner no probado aproveche sharing o asignación sliding reducida.
Con sliding optimizado a 1024, KV sería aproximadamente **0,438 GiB**, y el total
con las mismas reservas aún sería **11,908 GiB**, superior a los 10,822 disponibles.

Los 2 GiB de buffers son una **reserva de planificación**, no un pico medido ni un
requisito oficial. Se incluye conservadoramente el draft aunque se proyecte
`draft_num_predict=0`. No se equipara tamaño del archivo con consumo residente,
ni se afirma que el modelo inevitablemente cause OOM. Falta margen para **autorizar
una carga segura sin depender de optimizaciones no verificadas**.

Déficit frente a la cota conservadora: **3.515.181.056 bytes / 3,274 GiB de RAM**.
La reserva antigua de Qwen (8 GiB + 2 GiB) no se reutiliza como certificación de
seguridad para un modelo mayor. No se redujeron márgenes ni se intentó cargar para
descubrir experimentalmente si cabía.

## 3. Descarga y digest

**No se ejecutó `ollama pull`, `run`, `chat`, `generate`, `show` ni precarga.**
El modelo no figura entre los instalados. Se conservaron los dos Qwen previamente
instalados, sin inferencias ni descarga/descarga de residencia sobre ellos.

El digest de la capa del modelo principal declarado por el registro es:
`sha256:bb722270d54346adc198f213851dbe0207e87c3ecf2a0aff4d92262726215391`.
No se verificó su contenido local porque no se descargó. Las consultas de metadatos
no se contabilizan como inferencias; ningún token del modelo fue generado.

## 4. Configuración e integración

Se inspeccionaron `InferenceAdapter`, `AnalysisService`, `build_context`,
`response_schema`, `validate_report`, los controles Ollama y los contratos de riesgo,
incertidumbre y procedencia. **No se construyó ni activó un adaptador Gemma**, porque
el preflight obliga a detenerse antes de esa etapa. No se sustituyeron constantes
de Qwen ni se convirtió su transporte restringido en un cliente arbitrario.

Configuración prevista, **no ejecutada ni certificada**: política existente
`application-analysis-v1`, esquema `ModelReport`, `think=false`, `stream=false`,
`truncate=false`, `num_ctx=8192`, `num_predict=2048`, `temperature=0`, `seed=42`,
`num_gpu=0`, `num_thread=10`, `num_batch=256`, `draft_num_predict=0` y timeout
absoluto de 300 s. Las demás opciones seguirían `InferenceOptions` sin ajustes
entre casos; los defaults del tag anuncian draft=3 y muestreo diferente, que no
deben confundirse con parámetros efectivamente probados.

La futura adaptación mínima necesitaría validar digest, requisito del runtime y
control de pensamiento del tag concreto. No se presume compatible el chequeo de
`thinking.values` de Qwen sin verificarlo para Gemma. B y C tendrían exactamente
el mismo modelo, política, opciones y esquema; C solo añadiría recuperación 1A
verificada. A sigue sin IA. No se enviarían etiquetas 1B, referencias, respuestas B
ni adjudicaciones al LLM. Se mantienen intactos taxonomía B01–B07, validadores y
contratos. El bloqueo no justifica debilitar esas garantías.

## 5. Casos de desarrollo y resultados

**Ningún caso se ejecutó.** La siguiente cobertura prospectiva cabe en ocho
intentos usando exclusivamente fixtures sintéticas ya preparadas; no constituye
una campaña congelada y habilitada. No se abrió selección ni test final.

| Orden previsto | Fixture existente / modo | Referencia para revisión, nunca para el LLM | Resultado |
|---:|---|---|---|
| 1 | readiness `credential-control`, B | ∅; autenticación legítima y comentario adversario no prueban B07 | No intentado: preflight bloqueado |
| 2 | Gemini G02, B | B02; IEX funcional con entrada ligada | No intentado: preflight bloqueado |
| 3 | Gemini G04, B | ∅; ScriptBlock almacenado no invocado | No intentado: preflight bloqueado |
| 4 | readiness `download-invoke`, B | B01+B02; descarga y ejecución funcional | No intentado: preflight bloqueado |
| 5 | Gemini G08, B | B07; acceso a credenciales almacenadas, contrastado con caso 1 | No intentado: preflight bloqueado |
| 6 | fixture `AMBIGUOUS`, texto `& $unknown`, B | Comportamiento interno indeterminado; incertidumbre explícita, sin destino inventado | No intentado: preflight bloqueado |
| 7 | Gemini G03, C | ∅; recuperación no vacía de texto que solo se muestra | No intentado: preflight bloqueado |
| 8 | Gemini G06, C | B05+B06; recuperación no vacía de inventario/conectividad | No intentado: preflight bloqueado |

Fuentes: `experiments/model_readiness/diagnostics.py`,
`experiments/gemini_cases.py` y `backend/tests/behavior_detection/cases.py`.
El caso 1 cubre el control sin comportamientos y la autenticación legítima; el 5
aporta el contraste positivo B07. El presupuesto no permite añadir B para ambos C
sin retirar controles: no se promete una comparación pareada inexistente.

Por cada fila: intento real=0; respuesta/JSON/etiquetas predichas/evidencias
citadas/tiempo de inferencia/tokens/riesgo/incertidumbre/truncamiento=
**no observados**. Citas incorrectas, contradicciones, FP, FN e invenciones=
**no evaluables**, no cero. No se creó un ledger de intentos ficticios ni se
clasificó una ausencia de respuesta como fallo semántico del modelo.

Si se llegase a ejecutar esta cobertura, la congelación previa deberá ligar
los ocho textos exactos, orden, referencias externas al payload, dos recuperaciones
1A no vacías, configuración completa, prompt, esquema, fuentes y digest; un único
presupuesto durable de ocho intentos debe consumir cada intención antes de HTTP,
incluidos errores/truncamientos, sin reintentos ni cambios durante el lote.
Esa ejecución y su integración **no están realizadas por esta entrega bloqueada**.

## 6. Puerta de viabilidad y revisión semántica

Se define antes de cualquier inferencia futura una puerta de desarrollo pequeña,
separada de los umbrales históricos de selección científica:

1. Preflight seguro en cada llamada, margen RAM/compromiso ≥2 GiB durante toda la
   operación, exclusión de inferencias y ninguna interrupción de recursos.
2. Ocho respuestas completas utilizables por JSON, esquema, coherencia y procedencia;
   ningún truncamiento, reparación, reintento ni sustitución de un fallo.
3. B02 correcto en IEX y B01+B02 en el multietiqueta; sin etiquetas injustificadas
   en los controles 1, 3 y 7; B07 sustentado en 5, ausente en autenticación legítima.
4. Código no invocado tratado como inerte; incertidumbre explícita sobre el destino
   desconocido del caso 6, sin inventar comportamientos internos.
5. Cero reconstrucciones críticas inventadas y ninguna contradicción crítica entre
   operación, etiquetas, evidencia, riesgo e incertidumbre.
6. Al menos una respuesta C aceptada con cita correcta de recuperación 1A **no vacía**,
   vínculo al original y soporte semántico revisable. Ambas C se registran, incluidos
   rechazos; la mera inclusión de recuperación en el request no satisface esta puerta.

Parada inmediata ante un fallo claro de un control esencial o una infracción de
recursos/transporte; no completar el presupuesto para buscar resultados favorables.
Con un pase solo correspondería **candidato prometedor para selección independiente**.
No sería aprobación definitiva, estimación general de precisión ni comienzo de Fase 4.

La revisión semántica asistida debe registrar por hallazgo: relación operación/entrada,
invocación, citas originales/recuperadas y su raíz, citas erróneas, contradicciones,
FP/FN, reconstrucciones, riesgo e incertidumbre. Se distingue de la adjudicación
humana independiente, que no existe aquí. Una coincidencia literal no demuestra
soporte semántico. **Sin respuestas Gemma no hay revisión semántica observada.**

## 7. Comparación descriptiva con Qwen3.5 y Gemini

Se revisaron los cierres del piloto, Fase 2, preparación del modelo y los diagnósticos
Gemini, sin reescribirlos. El [cierre posterior de Qwen](pre_phase4_model_readiness.md)
registra **24/24 diagnósticos, 14 aceptados estructuralmente, 10 rechazados y 0/3 C
aceptados** en P0/P1/P3; el último C truncado tampoco es éxito. El piloto permanece
cerrado sin aprobación bajo su protocolo original.

Los defectos históricos incluyen B02 atribuido a mera construcción/impresión de texto,
decodificaciones inventadas, citas con fuente equivocada, prosa presentada como
reconstrucción y riesgo incoherente. El [cierre de Fase 2](phase2_closure.md) ya
advertía que la aceptación estructural no elimina estos errores. La cobertura
prospectiva busca precisamente esas fronteras; **Gemma no ha demostrado resolverlas**.

Gemini 3.8 terminó con HTTP 503 y Gemini 3.6 con HTTP 400; la causa del 400 sigue
indeterminada según [su diagnóstico](gemini_36_http400_diagnostic.md). El
[ledger de Gemini](gemini_36_viability.md) permanece en **4/12**. No se hicieron
llamadas a Gemini ni se enviaron datos a proveedores cloud. Las únicas consultas
externas fueron lecturas de metadatos públicos del modelo, no servicios de inferencia.

## 8. Resultado real de C

**C intentados con Gemma: 0. C aceptados: no evaluable.** No se generaron salidas,
no se validaron citas de Gemma y no existe evidencia de mejora frente a Qwen.
El éxito histórico con mocks prueba software, no desempeño de este candidato.
La obligación de observar C con recuperación verificable queda pendiente por el
bloqueo previo a la carga, sin reemplazarla por un control favorable.

## 9. Regresiones y preservación

Backend: **990/990 pruebas aprobadas**, cero fallos, errores u omitidas; 85,13 s,
con el entorno virtual existente del proyecto (pytest 9.2.0, Pydantic 2.14.2,
google-genai 2.34.0 y FastAPI 0.162.0). Todas las pruebas Gemini usan sus transportes
simulados; no se llamó a la API real.
[JUnit definitivo](../artifacts/local_model_gemma4_viability/backend_tests_venv.xml).

Las dos ejecuciones previas con el Python global se conservan como diagnóstico:
la primera encontró 172 errores de preparación por acceso al temporal predeterminado;
al usar un temporal propio quedaron 12 errores de setup/teardown por IDs extensos
en variables Windows y cinco módulos omitidos por SDK opcional ausente. El entorno
virtual correcto resolvió esas diferencias sin instalar paquetes ni cambiar tests.
No se presentan esas ejecuciones como regresiones funcionales ni se ocultan sus JUnit.

Frontend: **28/28 pruebas aprobadas**, tres archivos, 13,68 s. Se usó `npm.cmd`
porque la política de ejecución restringe el wrapper PowerShell `npm.ps1`; no se
modificó dicha política. [JUnit frontend](../artifacts/local_model_gemma4_viability/frontend_tests.xml).

Se conserva una línea base SHA-256 de **9545 archivos existentes**, incluidos
históricos, datasets, prompts, frontend, `.git/index` y `.git/HEAD`.
La evidencia nueva se guarda únicamente bajo `artifacts/local_model_gemma4_viability/`
y este informe. No se modifican pruebas existentes para obtener un pase.

La [verificación posterior](../artifacts/local_model_gemma4_viability/integrity_after.json)
encontró **cero archivos previos modificados o ausentes**, con índice y HEAD
idénticos. Esto incluye el ledger de Gemini, que permanece en 4/12. `git diff --check`
pasó; la rama sigue siendo `develop`. No hubo staging, commit, push, merge, rebase,
reset ni clean. Los cambios previos del usuario permanecen intactos.

## 10. Reproducción, límites y pendientes

Desde la raíz del proyecto:

```powershell
.venv/Scripts/python.exe artifacts/local_model_gemma4_viability/preflight_readonly.py
```

El [colector reproducible](../artifacts/local_model_gemma4_viability/preflight_readonly.py)
lee metadatos archivados, recursos nativos, procesos y solo `/api/version`, `/api/tags`,
`/api/ps` por loopback. Imprime JSON sin escribir el informe anterior, descargar,
cargar ni invocar modelos. Una nueva lectura no habilita inferencias automáticamente.
Los hashes/URLs de metadatos permiten auditar el cálculo; un tag remoto puede cambiar.

Regresión reproducible, sin inferencias reales:

```powershell
$env:PYTHONPATH = 'backend;.'
.venv/Scripts/python.exe -m pytest backend/tests -q --basetemp=artifacts/local_model_gemma4_viability/pytest_tmp_recheck
npm.cmd --prefix frontend test
```

El [recibo de decisión](../artifacts/local_model_gemma4_viability/decision.json)
conserva el bloqueo, los cero intentos y los hashes de las fuentes del cálculo.

No se midieron pico real, latencia, soporte efectivo de JSON/pensamiento ni carga
del modelo. No se verificó aceleración GPU y no se sustituyó el perfil CPU por uno
no probado. No se cambió BIOS, pagefile, defensas, runtime, Windows ni configuración
permanente. No se cerraron aplicaciones del usuario para obtener un preflight favorable.
Las muestras y sus URLs se trataron exclusivamente como texto: no se ejecutaron
PowerShell, código recuperado, Base64, C# ni salidas de modelos.

La única condición que justificaría reconsiderar la carga es disponer de un margen
de recursos suficiente y sostenido para el perfil documentado. No procede retocar
prompts ni iniciar otra auditoría semántica sin una sola respuesta real. Tampoco
se inicia ahora selección de 72 inferencias, evaluación final o Fase 4.

## 11. Decisión final

**BLOQUEADO OPERATIVAMENTE.** Gemma 4 12B es un identificador oficial compatible por
versión con el Ollama instalado; la sesión actual no permite autorizar su carga con
las reservas explicitadas. Se conserva intacto el presupuesto de ocho inferencias.
No hay base para declararlo prometedor, no apto por calidad o superior a Qwen.
La decisión inmediata es **no seguir con descarga/inferencias en este estado del equipo**.
