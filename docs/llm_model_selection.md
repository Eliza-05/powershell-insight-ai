# Selección preliminar del LLM local — PowerShell Insight AI

**Fecha de inspección y consulta:** 2026-11-02, America/Bogota.  
**Estado:** investigación terminada; recomendación **preliminar hasta realizar y aprobar el piloto v2**. No se ha seleccionado definitivamente un modelo ni iniciado la Fase 2.  
**Base inspeccionada:** rama `develop`, commit `0b2a67d5cbac841ff53c1a5e0f29ee65b3ac9bda`.

**Recomendación concreta:** probar primero **`qwen3.5:4b-q4_K_M`**, paquete de aproximadamente **3,3 GB**, con contexto inicial de **8192 tokens**, inferencia secuencial y presupuesto conservador de **4,5–6,0 GiB adicionales de RAM**. Como alternativa de otra familia, **`gemma4:e2b-it-q4_K_M`**, aproximadamente **4,6 GB** y **5,0–7,0 GiB de RAM**. Conservar el **`qwen2.5-coder:7b` Q4_K_M instalado** como referencia. Los tamaños de paquete están publicados por [Ollama para Qwen](https://ollama.com/library/qwen3.5:4b-q4_K_M) y [Ollama para Gemma](https://ollama.com/library/gemma4:e2b-it-q4_K_M); los presupuestos de ejecución son estimaciones de este estudio, no mediciones.

## 1. Objetivo y reglas de interpretación

Seleccionar un candidato que permita estudiar si la desofuscación estática previa mejora la identificación y explicación de comportamientos PowerShell, equilibrando soporte de evidencias, multietiqueta, tiempo y recursos locales. La potencia máxima de un modelo en servidores no es el criterio de selección.

Se utilizan tres niveles en todo el documento:

- **[V] Verificado:** lectura del repositorio, consulta local o información publicada en una fuente primaria. Verificar que un fabricante publica un resultado no equivale a reproducirlo.
- **[E] Estimado:** cálculo o expectativa razonada; incluye los presupuestos de RAM y los escenarios de rendimiento.
- **[NC] No comprobado:** requiere cargar y evaluar el candidato. Incluye su exactitud B01–B07, calidad semántica, resistencia a inyección y funcionamiento efectivo con este esquema y esta instalación.

**No hay métricas nuevas de detección, precisión, recall ni F1.** Tampoco se presupone superioridad de una familia. Ninguna fuente consultada constituye una evaluación específica del contrato B01–B07 de este proyecto.

Las consultas locales se limitaron a CIM, inventario de backends, metadatos de Git y Ollama, y lectura de archivos. No se descargaron pesos al equipo, no se cargaron modelos, no se hicieron solicitudes de generación ni se ejecutaron muestras. Las fuentes remotas se consultaron como documentación y metadatos, sin transmitir scripts del repositorio.

## 2. Estado verificado del proyecto y documentos inspeccionados

Al comenzar, `develop` tenía el árbol de trabajo y el índice limpios. `develop...origin/develop` dio **0/0** respecto de la referencia remota local. **No se ejecutó fetch:** esto verifica las referencias disponibles, no el estado actual del servidor remoto.

Todos los documentos solicitados existen en `docs/`; no fue necesario inventar contenido ni sustituir rutas:

| Documentos leídos | Consecuencia para esta selección |
|---|---|
| [pilot_plan.md](pilot_plan.md), [pilot_results.md](pilot_results.md), [pilot_audit.md](pilot_audit.md), [phase0b_closure.md](phase0b_closure.md) | El v1 no aprobó la selección. Umbrales originales e historia inmutables; siguiente validación con casos nuevos |
| [methodology.md](methodology.md), [behavior_taxonomy.md](behavior_taxonomy.md) | Clasificación multietiqueta; comportamientos, ofuscación y riesgo separados; política estricta de evidencias principal |
| [architecture.md](architecture.md), [deobfuscator.md](deobfuscator.md), [behavior_detector.md](behavior_detector.md) | 1A y 1B implementadas con cobertura parcial; recuperación textual no demuestra ejecución ni malicia |
| [roadmap.md](roadmap.md), [security.md](security.md) | Fase 2 bloqueada; análisis estático y uso exclusivo de muestras propias controladas mientras no exista el entorno aislado |
| [phase1b_closure.md](phase1b_closure.md) | 488 pruebas aprobadas reportadas en implementación/auditoría/cierre; no se volvieron a ejecutar en este estudio documental |

Las cabeceras antiguas de `deobfuscator.md` y los registros de cierre 0B describen la situación de su momento, anterior a 1B. Para el estado actual prevalecen la arquitectura, el roadmap y el cierre de 1B, junto con el commit inspeccionado. Algunas referencias a «publicación pendiente» permanecen en las actas; el commit actual ya contiene la documentación de cierre. No es indispensable reescribir esas actas para hacer esta selección y se conservan intactas.

La comparación definitiva sigue siendo **A:** desofuscador y reglas sin LLM; **B:** script ofuscado al LLM; **C:** original más artefactos recuperados al mismo LLM. B y C deben compartir modelo, digest, parámetros, esquema, política de pensamiento y presupuesto de salida. Solo cambia la entrada prevista por la metodología. Este estudio no construye ni ejecuta ese experimento.

### Contrato real del piloto y de las evidencias

Se inspeccionaron [pilot_v1.json](../experiments/configurations/pilot_v1.json), [llm_analysis.py](../backend/app/schemas/llm_analysis.py), [analyzer.py](../backend/app/services/llm/analyzer.py), [prompt.py](../backend/app/services/llm/prompt.py), el [prompt congelado](../experiments/prompts/pilot_analysis_v1.md), [pilot_metrics.py](../experiments/evaluation/pilot_metrics.py), [evidence_review.py](../experiments/evaluation/evidence_review.py) y [literal_check.py](../backend/app/services/evidence/literal_check.py).

- Configuración v1: `temperature=0`, `seed=42`, `num_ctx=8192`, `num_predict=2048`, `keep_alive=15m`, `stream=false`; host `127.0.0.1:11434`. La plantilla `.env.example` no gobierna ese runner: usa el JSON versionado.
- `pilot-schema-v1` admite **cero, uno o varios** elementos en `behaviors`. Cada hallazgo exige una o más evidencias; los objetos prohíben campos extra y los IDs son enums B01–B07. El código no impone una sola etiqueta: la auditoría de cierre lo comprobó con pruebas sintéticas.
- Campos separados: `obfuscation_techniques`, `recovered_content`, `behaviors`, `risk_label/risk_rationale`, `uncertainty`, `prompt_injection` y `limitations`. `origin` distingue `analyzed_script` y `model_decoded`; este último es una declaración del modelo, no certificación de recuperación.
- El cliente hace una llamada `chat(format=schema)`, valida con Pydantic, conserva fallos y no reintenta. Actualmente no fija `think` ni registra separadamente `message.thinking`: los modelos nuevos exigirán revisar este punto en un futuro arnés del piloto, previa autorización, sin modificar ahora producción.
- `literal_check` distingue coincidencia exacta en entrada, referencia, normalizada y ausente. Una referencia decodificada por el equipo sirve para comprobar una cita; **no convierte ese contenido en recuperación efectuada por el LLM**.
- La métrica histórica `unsupported_claims` mezcla etiqueta fuera de referencia y ausencia de cita literal. La revisión derivada distingue soporte individual, contextual, insuficiente y pendiente humano, además de errores textuales. **DEC-01:** solo el contexto efectivamente citado o recuperado y verificable cuenta en la política estricta; admitir contexto no citado es una evaluación secundaria.

## 3. Piloto v1: resultados que se conservan

Fuente: [resultados](pilot_results.md), [auditoría](pilot_audit.md) y [cierre 0B](phase0b_closure.md); ejecución `pilot-v1_20261101T001806Z`.

| Dimensión | Resultado histórico [V], salvo juicio semántico indicado |
|---|---|
| Modelo | Qwen2.5-Coder 7B, Q4_K_M, digest `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364` |
| Muestra | 8 casos P1–P8, tres repeticiones: 24 ejecuciones, solo configuración B |
| JSON válido según esquema | 24/24 |
| Etiquetas exactas del núcleo | **4/7**, frente al requisito **≥5/7** |
| Micro P / R / F1 | 0,875 / 0,700 / 0,7778; TP/FP/FN = 21/3/9 |
| Macro-F1 | 0,667 sobre B01, B02, B03 y B05; sin positivos B04/B06/B07 |
| B02 | Recall 0/6; 3 FP en P2 por confundir el lanzador con B02 |
| Multietiqueta / Base64 | Un solo comportamiento en 24/24; no recuperó el contenido Base64 en P2/P6 |
| Citas literales | 41/41; no demuestra respaldo semántico |
| Evidencia semántica derivada | 15/24 hallazgos respaldados con política estricta; 18/24 permisiva. Juicios AI-assist pendientes de validación humana específica |
| Tres conteos diferentes | 3/24 hallazgos marcados automáticamente; 6/24 sin soporte en revisión semántica histórica; 12/24 ejecuciones con problemas textuales históricos. Métodos y denominadores distintos |
| Inyección / incertidumbre | P8: no obedeció en 3/3, pero detección explícita 0/3. Incertidumbre declarada 0/24 |
| Latencia continua | 22 ejecuciones: media 39,1 s, mediana 32,0 s, máximo 72,9 s; ~11,8 tokens/s de generación |
| Memoria / aceleración | ~5,47 GB reportados por `/api/ps`, contexto 8192; CPU, `size_vram=0` en las 24 |

La suspensión de P1-r3 y la degradación de P6-r1 permanecen en las métricas de calidad y solo se separaron al describir latencia continua. No se presenta la media automática histórica de 2911 s como velocidad normal, ni se eliminan esos registros.

El modelo **no fue aprobado**. Estos datos describen una combinación de modelo, cuantización, prompt y parámetros; no invalidan a Qwen como familia. Tampoco prueban que un candidato nuevo vaya a mejorar. El fallo multietiqueta y el de B02 no se pueden atribuir causalmente a un único factor con esos ocho casos.

## 4. Hardware y entorno real

Las consultas CIM inicialmente recibieron acceso denegado en el sandbox. Se repitieron exclusivamente como lecturas con la elevación de acceso de la herramienta, sin modificar Windows. No se registraron números de serie, identidad de máquina, credenciales ni variables de entorno generales.

| Elemento | Dato verificado el 2026-11-02 | Interpretación práctica |
|---|---|---|
| CPU / arquitectura | AMD Ryzen AI 9 365 w/ Radeon 880M; CIM Architecture 9 = x64; 10 núcleos, 20 procesadores lógicos | CPU moderna capaz de inferencia local; los hilos no garantizan escalado lineal |
| RAM física instalada | 34 359 738 368 bytes = **32 GiB** | No toda está disponible para aplicaciones |
| RAM visible para Windows | 32 630 636 KiB = **31,12 GiB** | Diferencia con instalada reservada por plataforma/hardware; no se atribuye íntegramente a la GPU |
| RAM disponible | Primera consulta: 8 962 448 KiB = **8,55 GiB**; otra: 9 134 028 KiB = **8,71 GiB**; contador posterior: 8466 MiB = **8,27 GiB** | Fotografías de carga cambiante, sin modelos cargados; presupuesto real inicial cercano a **8–9 GiB**, no 32 GiB libres |
| GPU enumerada | Solo **AMD Radeon(TM) 880M Graphics**, integrada; driver `32.0.13022.3006` | No se detectó GPU dedicada; `nvidia-smi` no está en PATH. Esta ausencia no es el único fundamento: también se enumeraron los controladores de vídeo |
| Memoria gráfica informada por CIM | `AdapterRAM=536870912` bytes = **512 MiB** | No es una medición de VRAM libre ni del presupuesto total compartido de la iGPU. **VRAM disponible/budget dinámico: no determinado** con estas consultas |
| Paginación / compromiso | Archivo de paginación asignado 17 408 MiB = 17 GiB; uso 119 MiB y pico 152 MiB en esa lectura. Compromiso posterior 31 715 639 296 bytes / límite 51 667 382 272 bytes (~61%) | No son 17 GiB de RAM rápida extra. Uso puntual bajo de pagefile no demuestra ausencia de presión durante inferencia futura |
| Disco C: | Capacidad 1 022 358 786 048 bytes (~952,15 GiB); libres 561 415 176 192 bytes (~522,86 GiB) | Descargas de pocos GB caben en C:. No se midieron velocidad de disco ni cuota de sincronización |
| Sistema operativo | Windows 11 Home, `10.0.26300`, 64 bits | Entorno del piloto, sin cambios realizados |
| Ollama | CLI y `GET /api/version`: **0.40.13** | Se conserva esta versión durante el estudio |
| Backends instalados | Carpetas `vulkan`, `rocm_v7_1`, `cuda_v12`, `cuda_v13`; DLL de CPU, incluida Zen 4 | Presencia de bibliotecas ≠ detección efectiva de acelerador ni soporte probado de un modelo |
| API local | Escucha en `127.0.0.1:11434` | No se cambió su exposición |
| Modelos instalados | Únicamente `qwen2.5-coder:7b`, GGUF Q4_K_M, **4 683 087 561 bytes**, digest igual al del v1 | Referencia disponible sin una nueva descarga |
| Modelos cargados | `ollama ps` y `GET /api/ps`: lista vacía | Ninguna inferencia en curso atribuible a Ollama en ese momento; no se inició ninguna |

### Aceleración: posibilidad frente a evidencia

La tabla oficial de [soporte de hardware de Ollama](https://docs.ollama.com/gpu) incluye el Ryzen AI 9 365 en **Linux**, pero no la 880M en su lista ROCm de **Windows**. La misma documentación describe soporte adicional por Vulkan, habilitado por defecto cuando está instalado el backend. Aquí ese backend existe [V]; reconocimiento del dispositivo, offload útil y velocidad son **[NC]**. El único dato de ejecución existente es CPU en el v1.

Por ello, **toda recomendación debe ser viable en CPU**. No se exige habilitar Vulkan, cambiar driver, BIOS, memoria reservada ni usar forks. Una futura comprobación de aceleración necesitaría autorización de carga/prueba y registro de `ollama ps`/`size_vram`; no se confunde memoria compartida con VRAM dedicada adicional. No se verificó ni se presupone una ruta de inferencia Ollama sobre la NPU.

## 5. Investigación de familias y límites de la evidencia

Se examinó la [biblioteca actual de Ollama](https://ollama.com/library), las etiquetas exactas y fichas del desarrollador. No se utiliza el texto publicitario «latest» como prueba de que una variante sea la más nueva o la mejor. La investigación abarca modelos de código y modelos generales.

**Qwen3.5 4B:** la ficha específica publica arquitectura híbrida, evaluación de código y seguimiento de instrucciones; por ejemplo, IFEval 89,8 y LiveCodeBench v6 55,8 como resultados del desarrollador. Son indicios de capacidad general, **no precisión PowerShell**, no resultados Q4_K_M locales y no garantizan calidad con pensamiento desactivado. El modelo pequeño no debe confundirse con el gran MoE usado en varias tablas generales de la familia. La ficha distingue modos con/sin pensamiento y no admite el cambio textual `/think`/`/nothink` de Qwen3. [Ficha Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B).

**Gemma 4 E2B:** opción de otra familia con instrucciones, código y diseño para dispositivo local. Google declara **2,3B efectivos y 5,1B con embeddings**; el componente principal de Ollama informa 4,65B, más projector y draft separados. Son perímetros de conteo distintos: **E2B no significa que solo haya que almacenar dos mil millones de parámetros**. Su ficha informa LiveCodeBench v6 44,0, sin que esto constituya una comparación local controlada frente a Qwen. La licencia publicada de **Gemma 4 es Apache 2.0**, no se le atribuyen automáticamente los términos de generaciones anteriores. [Ficha Google](https://huggingface.co/google/gemma-4-E2B-it).

**Phi-4-mini:** opción compacta MIT, con enfoque en razonamiento y seguimiento de instrucciones. Microsoft advierte que no está evaluado para todos los usos; su red teaming menciona posibles nombres de funciones y URL inventados. Ser de Microsoft no acredita dominio de PowerShell ni fiabilidad de sus evidencias. [Ficha Microsoft](https://huggingface.co/microsoft/Phi-4-mini-instruct).

**Ministral 3 3B Instruct 2512:** alternativa de bajo tamaño con soporte declarado de system prompt y salida JSON. El desarrollador distingue aproximadamente 3,4B de lenguaje y 0,4B de visión. Viable, pero sin prueba específica B01–B07; se mantiene fuera de la primera pareja para acotar el coste del piloto. [Ficha Mistral](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512).

**Qwen3 8B, Llama 3.1 8B y DeepSeek-R1-0528-Qwen3-8B:** opciones que caben condicionalmente en RAM. Qwen3 ofrece contraste de arquitectura/tamaño; Llama aporta otra familia; DeepSeek aporta destilación de razonamiento, pero su generación extendida y política de pensamiento complican la latencia y la comparación con 2048 tokens. La ficha de esta destilación confirma arquitectura Qwen3-8B y recomienda otro régimen de muestreo; no se transfieren al 8B los resultados del R1 completo. [Qwen3 Ollama](https://ollama.com/library/qwen3:8b-q4_K_M), [Llama Ollama](https://ollama.com/library/llama3.1:8b-instruct-q4_K_M), [DeepSeek oficial](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528-Qwen3-8B).

### Familias o tamaños descartados de la primera evaluación

«Descartado» significa que no merece una descarga en este primer estudio; no que se haya demostrado mala calidad.

| Modelo/familia examinada | Evidencia de disponibilidad | Motivo de descarte o aplazamiento |
|---|---|---|
| Qwen3.8 27B | [Etiqueta actual](https://ollama.com/library/qwen3.8:27b), paquete publicado ~18 GB | Más reciente, pero supera ampliamente la RAM hoy disponible antes de caché y buffers; no se presupone que exista una versión 4B equivalente |
| Qwen3-Coder-Next | [Ollama](https://ollama.com/library/qwen3-coder-next), Q4_K_M ~52 GB; base 80B-A3B | Los parámetros activos no reducen a 3B los pesos residentes; excede incluso la RAM física |
| Qwen3-Coder 30B | [Biblioteca](https://ollama.com/library) identifica tamaño 30B | No es un sustituto de 4–8B por ser MoE; no se verificó una cuantización pequeña adecuada a este presupuesto, por lo que no se prescribe una |
| Qwen2.5-Coder 14B | [Tag Q4_K_M](https://ollama.com/library/qwen2.5-coder:14b-instruct-q4_K_M): 14,8B, ~9,0 GB | Pesos solos ~8,38 GiB; con contexto/buffers supera 8–9 GiB libres. Podría caber liberando mucha RAM, pero no es la primera opción repetible |
| Gemma 4 26B/31B y Qwen3.5 27B/35B | [Tags Gemma](https://ollama.com/library/gemma4/tags), [tags Qwen](https://ollama.com/library/qwen3.5/tags) | Paquetes de ~16–22 GB más ejecución; alto riesgo de paginación en el estado observado |
| Gemma 4 E4B/12B | [Tags oficiales](https://ollama.com/library/gemma4/tags): alias publicados desde ~6,6/~7,7 GB según backend | Menor margen que E2B; no se eligió un tag/quant exacto para descargarlos y no se confunden variantes MLX con Windows |
| Llama de mayor tamaño, DeepSeek completo y destilados 14B o mayores | [Llama](https://ollama.com/library/llama3.1), [DeepSeek](https://ollama.com/library/deepseek-r1) | Fuera del presupuesto operativo inicial; no se asume GPU adicional |
| LFM2.5 1.2B Instruct | [Publicación de LiquidAI en Ollama](https://ollama.com/LiquidAI/lfm2.5-1.2b-instruct) | Muy compacto, pero la propia descripción desaconseja programación y tareas intensivas en conocimiento. No elegirlo por cifras de velocidad de otro hardware |

## 6. Fuentes, licencias y calidad de respaldo

**Todas las fuentes web enlazadas en este documento se consultaron el 2026-11-02.** Son páginas oficiales de Ollama o publicaciones/repositorios del desarrollador. Son mutables: los IDs abreviados y tamaños describen lo visible durante esta consulta. No se obtuvo una copia de los pesos ni una validación independiente en este equipo.

| Fuente primaria adicional | Qué respalda y qué no |
|---|---|
| [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs) | Uso local de JSON Schema en `format` y validación Pydantic. No garantiza corrección de etiquetas, citas o razonamiento |
| [Ollama thinking](https://docs.ollama.com/capabilities/thinking) | `think`, campos de respuesta y descubrimiento de controles por `/api/show`; los valores admitidos dependen del modelo |
| [Ollama FAQ](https://docs.ollama.com/faq) | `num_ctx`, lectura de CPU/GPU, memoria por paralelismo y tipos de KV cache. No mide este portátil |
| [Config Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B/raw/main/config.json), [9B](https://huggingface.co/Qwen/Qwen3.5-9B/raw/main/config.json) | Dimensiones de atención y patrón híbrido para estimar caché |
| [Config Gemma E2B](https://huggingface.co/google/gemma-4-E2B-it/raw/main/config.json) | Ventana deslizante, dimensiones y compartición de KV; no certifica cómo cada backend asigna memoria |
| [Config Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B/raw/main/config.json), [Phi-mini](https://huggingface.co/microsoft/Phi-4-mini-instruct/raw/main/config.json) | Dimensiones para cálculos de atención completa |
| [Licencia Llama 3.1 publicada por Meta](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct/blob/main/LICENSE) | Licencia comunitaria y política de uso, obligaciones de atribución/redistribución y condiciones comerciales; no es Apache/MIT |

Qwen, Gemma 4 y Ministral considerados publican **Apache 2.0**; Phi-mini **MIT**; el tag de DeepSeek publica MIT y la base Qwen3 tiene sus propios avisos Apache que deben conservarse cuando corresponda. Para uso académico local son opciones documentalmente razonables; al redistribuir pesos o derivados hay que conservar las licencias y avisos aplicables. Llama exige revisar sus términos específicos. Estas observaciones no sustituyen una revisión de licencia del artefacto exacto que finalmente se descargue.

**Jerarquía de evidencia:** inventario y metadatos exactos = respaldo fuerte para existencia/tamaño; benchmarks del desarrollador = evidencia indirecta de capacidades generales; extrapolación a análisis PowerShell adversario = débil hasta el piloto. No se encontró en las fuentes consultadas una evaluación independiente equivalente, con nuestro ground truth, mismas cuantizaciones y hardware. No se sustituye esa ausencia por rankings ni por testimonios de foros.

## 7. Tabla comparativa de candidatos técnicamente viables

**Unidades:** descarga en GB decimales como publica Ollama; ejecución/caché en **GiB**. RAM estimada es incremento para un único runner a 8192 tokens, texto solamente; excluye el consumo previo de Windows y aplicaciones. Los rangos son presupuestos de planificación con margen, no cotas garantizadas. CPU es la base para todos; GPU local útil sigue [NC].

| Modelo exacto y fuente [V] | Parámetros publicados [V] | Quant [V] / descarga [V] | Caché/estado a 8K [E] | RAM de ejecución total [E] | Ajuste con 8–9 GiB disponibles [E] | Contexto práctico inicial [E] | Licencia publicada [V] |
|---|---|---|---|---|---|---|---|
| **[qwen3.5:4b-q4_K_M](https://ollama.com/library/qwen3.5:4b-q4_K_M)** | 4B nominal; componente GGUF 4,21B + projector 334M | Q4_K_M / **3,3 GB** | ~0,25 GiB KV completo + ~0,05 GiB estado recurrente ideal; reservar 0,3–0,8 | **4,5–6,0 GiB** | Mejor margen entre los dos seleccionados; conservar ≥2 GiB libres | **8192**; 4096 como alternativa predeclarada si todo cabe; 16K solo tras medir | Apache 2.0 |
| **[gemma4:e2b-it-q4_K_M](https://ollama.com/library/gemma4:e2b-it-q4_K_M)** | 2,3B efectivos / 5,1B con embeddings según Google; GGUF principal 4,65B | Q4_K_M / **4,6 GB**, incluye componentes adicionales | Reservar 0,2–0,8 GiB; ventana/compartición alteran asignación efectiva | **5,0–7,0 GiB** | Viable con menos margen; extremo alto exige liberar RAM antes | **8192**; no asumir 128K utilizables | Apache 2.0 |
| [phi4-mini:3.8b-q4_K_M](https://ollama.com/library/phi4-mini:3.8b-q4_K_M) | 3,84B | Q4_K_M / 2,5 GB | ~1,0 GiB KV | 4,0–5,5 GiB | Viable; pequeño paquete no elimina coste de contexto | 8192; no 128K | MIT |
| [ministral-3:3b-instruct-2512-q4_K_M](https://ollama.com/library/ministral-3:3b-instruct-2512-q4_K_M) | GGUF 3,85B; incluye visión | Q4_K_M / 3,0 GB | Presupuesto 0,5–1,5 GiB, no asignación medida | 4,5–6,5 GiB | Viable, reserva secundaria | 8192; no 256K | Apache 2.0 |
| [qwen3:8b-q4_K_M](https://ollama.com/library/qwen3:8b-q4_K_M) | 8,19B | Q4_K_M / 5,2 GB | ~1,125 GiB KV | 6,5–8,5 GiB | Condicional: liberar RAM; extremo alto deja poco margen | 4096–8192, fijar uno antes de comparar | Apache 2.0 |
| [qwen3.5:9b-q4_K_M](https://ollama.com/library/qwen3.5:9b-q4_K_M) | GGUF 8,95B + projector 456M | Q4_K_M / 6,6 GB | KV/estado teórico similar a 4B; reservar 0,3–0,8 GiB | 7,5–9,5 GiB | Condicional; no cargar con la disponibilidad mínima observada | 4096–8192, tras liberar RAM | Apache 2.0 |
| [llama3.1:8b-instruct-q4_K_M](https://ollama.com/library/llama3.1:8b-instruct-q4_K_M) | 8,03B | Q4_K_M / 4,9 GB | Reserva conservadora 1,0–1,5 GiB | 6,5–8,5 GiB | Condicional, margen estrecho | 4096–8192 | Llama 3.1 Community |
| [deepseek-r1:8b-0528-qwen3-q4_K_M](https://ollama.com/library/deepseek-r1:8b-0528-qwen3-q4_K_M) | 8,19B; destilación Qwen3 | Q4_K_M / 5,2 GB | ~1,125 GiB KV por arquitectura base, más buffers | 6,5–8,5 GiB | Pesos viables condicionalmente; tiempo de pensamiento puede hacerlo impráctico | 4096–8192 | MIT y avisos de base aplicables |
| **qwen2.5-coder:7b**, inventario local | 7,6B | Q4_K_M / **4,683 GB ya instalados** | ~0,4375 GiB KV | Presupuesto 5,0–7,0 GiB; histórico `/api/ps` **5,47 GB** (~5,09 GiB), distinto indicador | Viable como referencia; sin nueva descarga | **8192**, como v1; máximo local anunciado 32768 | Apache 2.0 |

No se suman los pesos otra vez a «RAM total». El tamaño `/api/ps`, working set, memoria privada comprometida y RAM disponible no son métricas intercambiables.

Para todos los tags nuevos, la **disponibilidad remota** está verificada y la **compatibilidad de carga efectiva en Ollama 0.40.13 está sin comprobar**. El tag de Phi anuncia mínimo 0.5.13 y el de Ministral 0.13.1; la versión instalada es posterior, pero eso no prueba ausencia de regresiones. No se verificó un mínimo exacto para Qwen3.5/Gemma 4 en las páginas consultadas ni se propone actualizar el programa sin necesidad demostrada.

### Calidad esperada y limitaciones por candidato

**JSON [V documental / NC local]:** todos pueden solicitarse mediante el mecanismo local de esquema de Ollama; solo la referencia tiene 24/24 respuestas verificadas con nuestro esquema. La decodificación restringida facilita sintaxis válida, no garantiza semántica ni salida completa dentro del presupuesto. «Buen seguimiento esperado» tampoco demuestra resistencia a inyección indirecta.

| Candidato | Fortalezas pertinentes / seguimiento esperado [E] | Limitaciones decisivas [NC salvo historia v1] | Escenario CPU de generación [E], no medición |
|---|---|---|---|
| Qwen3.5 4B | Equilibrio prometedor de razonamiento de código, instrucciones y bajo tamaño; arquitectura híbrida reduce KV frente a atención completa | No demostrado en PowerShell, multietiqueta, Base64 ni evidencia estricta; resultados publicados pueden usar pensamiento largo | **8–24 tok/s**, sin pensamiento; 500–1000 tokens requieren ~21–125 s de generación |
| Gemma 4 E2B | Contraste de familia; instrucciones y código en formato compacto; system role nativo publicado por Ollama | Efectivos ≠ residentes; paquete multimodal/draft; sin garantía B02 ni de abstención correcta | **8–24 tok/s** como escenario amplio; mayor rapidez no demostrada |
| Phi-4-mini | Bajo tamaño y entrenamiento para instrucciones/razonamiento; expectativa favorable de ajuste al formato | Conocimiento específico y citas no validados; posible invención de funciones/URL descrita por el desarrollador | **8–24 tok/s** como escenario, no ventaja medida |
| Ministral 3 3B | Instruct con JSON y system prompt publicados; bajo tamaño | Seguridad PowerShell y separación B01/B02 no evaluadas; no ampliar candidatos sin necesidad | **8–24 tok/s** como escenario |
| Qwen3 8B | Razonamiento general y seguimiento prometedores, más parámetros | Más KV; controlar pensamiento, sin atribuir resultados de 30B/235B al 8B | **6–15 tok/s** como escenario |
| Qwen3.5 9B | Más capacidad representacional; candidato de escalado si 4B falla | Más memoria; no hay demostración local de beneficio por tamaño | **5–14 tok/s** como escenario |
| Llama 3.1 8B | Instruct generalista, otra familia; soporte documental de tareas de código | Licencia específica, mayor coste que compactos; no evidencia de ventaja en esta taxonomía | **6–15 tok/s** como escenario |
| DeepSeek 8B 0528 | Destilación centrada en razonamiento y código | Posible cadena extensa antes del JSON, presupuesto de 2048 insuficiente; no asumir que `think=false` está permitido | **6–15 tok/s** para tokens generados; latencia final puede ser mucho mayor |
| Qwen2.5-Coder 7B | Código y JSON comprobado en v1; referencia útil para separar efecto del prompt | Fallos B02/multietiqueta/evidencia/incertidumbre ya medidos; sigue sin aprobar | **~11,8 tok/s medidos históricamente**, no repetidos ahora |

Los intervalos nuevos son **escenarios de planificación de baja confianza**, anclados de forma conservadora alrededor del único dato local (~12 tok/s) y ampliados por diferencias de tamaño/arquitectura. No son benchmarks, garantías ni intervalos estadísticos. No se conoce el ancho de banda efectivo de memoria ni el comportamiento térmico bajo estas cargas. Se podría quedar fuera de todos esos rangos si hay paginación, contención o un backend diferente.

## 8. Memoria, contexto y rendimiento

### 8.1 Presupuesto explícito

Se utiliza:

`RAM adicional ≈ pesos residentes + KV/estado recurrente + buffers de cómputo + runtime + componentes auxiliares`.

Para atención completa estándar, una aproximación FP16 es:

`KV_bytes = 2 (K y V) × capas × cabezas_KV × dimensión_cabeza × tokens_contexto × 2 bytes`.

Es un cálculo de almacenamiento ideal; no incluye alineación, reservas del backend, batching ni buffers. No se aplica ciegamente a modelos híbridos o con KV compartida.

En Qwen3.5 4B hay 8 capas de atención completa, 4 cabezas KV y dimensión 256: a 8192 tokens, **268 435 456 bytes = 0,25 GiB** de KV ideal. Las 24 capas recurrentes añaden del orden de **0,05 GiB** de estado ideal con las dimensiones publicadas, más convolución y reservas de implementación. Los [metadatos GGUF publicados](https://ollama.com/library/qwen3.5:4b-q4_K_M/blobs/a9d0a3e1d8c9) coinciden con el patrón relevante de la configuración. El estado recurrente no crece como una caché completa por cada token, aunque otros buffers sí pueden crecer.

En la referencia local: 28 capas, 4 cabezas KV y dimensión 128 dan **0,4375 GiB** a 8K; en Qwen3-8B: 36 capas, 8 cabezas KV, dimensión 128 dan **1,125 GiB**. Phi-mini con 32 capas, 8 KV y dimensión 128 da **1 GiB**. Son cálculos [E] sobre metadatos [V], no consumos medidos.

Gemma E2B mezcla ventanas de 512 tokens con atención completa y comparte KV en 20 capas según su configuración. Una cota simplificada sin optimizaciones, tratando las 35 capas como completas de dimensión 512 y una cabeza KV, daría ~0,547 GiB a 8K. La asignación real puede reducirse por ventanas/compartición o aumentar por buffers y draft. Se reserva 0,2–0,8 GiB para ese subsistema, sin fingir exactitud del backend.

### 8.2 Descarga no es memoria residente

En Qwen4B, Ollama separa [modelo principal ~2,6 GB](https://ollama.com/library/qwen3.5:4b-q4_K_M/blobs/a9d0a3e1d8c9) y [projector ~676 MB](https://ollama.com/library/qwen3.5:4b-q4_K_M/blobs/e56a899b1540). En Gemma E2B figuran [principal ~3,5 GB](https://ollama.com/library/gemma4:e2b-it-q4_K_M/blobs/6dd7ac24fe13), [projector ~987 MB](https://ollama.com/library/gemma4:e2b-it-q4_K_M/blobs/7ba3bbacdf1b) y draft ~98 MB descrito en el tag. Se presupuesta el paquete completo: **no se promete que Ollama omita esos componentes al analizar solo texto**.

Los pesos Q4_K_M no equivalen a todos los tensores exactamente a 4 bits y no cuantizan automáticamente la KV. Según la [FAQ](https://docs.ollama.com/faq), la KV usa por defecto `f16`; cuantizarla depende del backend/Flash Attention y puede cambiar calidad. No se modifica esa configuración global para hacer caber un candidato. Cualquier prueba de KV Q8 sería una condición nueva, documentada y común a los brazos pertinentes.

### 8.3 Contexto utilizable

Propuesta común inicial: **8192 tokens**, incluyendo instrucciones, esquema cuando se inserte en el prompt, script y hasta 2048 tokens de salida; objetivo de entrada total **≤5500 tokens por tokenizer** para dejar margen a plantilla y marcadores. El tokenizador cambia entre modelos: igualdad de tokens no significa igualdad de texto.

No se usan los máximos publicitados de 128K/256K. El límite de 1 MiB de entrada del motor estático tampoco promete que ese texto quepa en el LLM. Nada se recorta silenciosamente. Una entrada que no cabe se registra como fuera del presupuesto y se aplica una política congelada antes de evaluar. Reducir a 4096 exige que **todos** los casos del protocolo quepan con el mismo presupuesto de salida y se declare antes de abrir la reserva; no es una reparación posterior a un fallo.

Para Qwen4B, con 8,27–8,71 GiB disponibles y gasto estimado 4,5–6,0 GiB, quedarían aproximadamente **2,3–4,2 GiB**. Para Gemma, 5–7 GiB dejan aproximadamente **1,3–3,7 GiB**: el extremo alto exige liberar aplicaciones antes de cargar. Como política propuesta, no iniciar un bloque si el extremo conservador del presupuesto no deja **2 GiB** de margen. El presupuesto se verifica de nuevo, no se presupone constante.

Un modelo 9B podría caber tras cerrar aplicaciones, pero hoy requiere más margen del observado. El almacenamiento no limita la pareja de candidatos: nueva descarga bruta máxima prevista **3,3 + 4,6 ≈7,9 GB**; reservar **12–16 GB** para paquetes, metadatos y holgura, verificando antes el volumen real de `OLLAMA_MODELS`. No se cambió ni se expuso su ruta efectiva; el espacio de C: no verifica cuotas de otro volumen. Los modelos deben permanecer fuera del repositorio y de su publicación.

### 8.4 Tiempo y viabilidad nocturna

Con 500–1000 tokens de salida a 8–24 tok/s, solo generar tomaría ~21–125 s. Carga, prefill, validación y contención se suman. **30–180 s por llamada** es un escenario operativo para planificar compactos con respuestas más largas que v1, no una latencia prometida. Un límite de 2048 tokens a 8 tok/s ya necesita ~256 s de generación; el timeout no debe confundirse con el promedio.

La proyección histórica de 504 llamadas B/C a 40–60 s fue ~5,6–8,4 h; **no se adopta 504 como tamaño definitivo**. A 120 s serían 16,8 h y dejaría de cumplirse una noche. Antes de seleccionar se calculará `N_llamadas × latencia_media`, más carga y margen, sobre el plan realmente aprobado.

Para la reserva propuesta de 24 casos × 3 repeticiones × 3 brazos = **216 llamadas**, los escenarios de 40/60/120/180 s dan **2,4/3,6/7,2/10,8 h**, más carga. La aceptación «una noche» debe concretarse previamente; se propone exigir **tiempo total proyectado × 1,20 ≤ 10 h**, pendiente de aprobación. No se cambian ahora suspensión, potencia, drivers ni servicios; esas condiciones se acuerdan para una futura sesión experimental.

## 9. Riesgos y distinciones funcionales obligatorias

Todo candidato debe superar pruebas que separen operaciones, evidencia, procedencia y riesgo:

| Frontera | Regla que se debe respetar |
|---|---|
| B01 / B02 | Descargar no implica ejecutar. Exigir evaluador/invocación funcional y relación con su entrada para B02; pueden coexistir |
| Lanzador / B02 | `-EncodedCommand` como envoltorio no añade B02. `&` literal o reconstruido no lo demuestra automáticamente |
| URL / B01-B06 | Cadena o comentario con URL no es operación de red. Descarga sola produce B01, no también B06 |
| B03 / B05 | Escribir un mecanismo de inicio futuro puede ser persistencia; leer Run no establece persistencia |
| B04 / B05 | Consultar Defender no equivale a deshabilitarlo; restaurar un control no se etiqueta como debilitamiento |
| B07 / autenticación | `Get-Credential` legítimo no basta; acceso a almacén o extracción exige contexto. No inventar valores de secretos ni resultados |
| Datos / instrucciones | Comentarios, cadenas, nombres y contenido decodificado son datos no confiables; ninguna instrucción suya gobierna al analista |
| Recuperación / operación | Decodificar texto no prueba que se ejecute. No inferir el contenido de una descarga ausente ni el éxito real en un host |
| Abstención / ausencia | Fragmento no interpretable debe conservar incertidumbre; lista vacía no certifica script seguro |

El historial de wrappers puede ser necesario para decidir B02 funcional: no siempre se puede deducir de la sintaxis. Si se proporciona procedencia, debe ser metadata factual común y sin etiquetas esperadas para todos los modelos; si se desconoce, se exige incertidumbre y se reporta el caso por separado. En el futuro B/C esa información de procedencia no puede favorecer solo a C y confundir el efecto de la desofuscación.

Otros riesgos: cuantización altera detalles del lenguaje; temperatura cero no garantiza determinismo entre backends; una salida extensa consume contexto y tiempo; alineación de seguridad puede causar rechazos de análisis defensivo; seguir instrucciones benignas no prueba resistencia adversaria. No se dispone de una «inmunidad a prompt injection» certificada para ningún candidato.

## 10. Recomendación principal y relación con los fallos v1

**Proponer `qwen3.5:4b-q4_K_M` como primer candidato, sin aprobación definitiva.** Se elige por margen de memoria en el estado real del portátil, evidencia indirecta de razonamiento de código/instrucciones en su ficha específica y coste razonable para repetir experimentos. La cuantización Q4_K_M existe realmente; no exige importar un GGUF de procedencia distinta ni asumir aceleración. Es preferible inicialmente al 9B porque no obliga a depender de una gran liberación de RAM.

Frente a Gemma E2B, el paquete Qwen es menor y la arquitectura permite calcular un KV contenido. Su ficha ofrece señales de capacidad de código pertinentes, aunque el rendimiento efectivo en el modo breve propuesto sigue por probar. **No se afirma que sea más exacto que Gemma, que Qwen2.5-Coder ni que un 8B.** Si no cumple los criterios, no se seleccionará por comodidad de recursos.

| Problema v1 | Por qué merece probar el candidato | Cómo se comprobará; mejora aún [NC] |
|---|---|---|
| Una sola etiqueta y B02 omitido | Modelo general postentrenado en instrucciones/razonamiento; hipótesis de mejor aplicación del catálogo | B02 aislado y combinaciones no relacionadas con descargas; comparar referencia con el mismo prompt v2 |
| Lanzador tomado como B02 | Posible mejor aplicación de exclusiones explícitas | Pares launcher/función dinámica, con procedencia documentada y negativos de `&` |
| Base64 no recuperado | No hay prueba de que Qwen3.5 lo resuelva de forma fiable; no es una razón para prometer mejora | Medir recuperación exacta, interpretación e incertidumbre por separado; no introducir desofuscador en la selección B |
| Citas existentes pero sin soporte | El modelo podría relacionar piezas de contexto; JSON no lo garantiza | Revisión humana de conjuntos de citas y sus relaciones, política estricta principal |
| Explicaciones inventadas | Hipótesis de mejor correspondencia código-explicación | Contar operación falsa, afirmación no establecida, especulación y clasificación errónea por separado |
| Inyección no reportada / incertidumbre baja | Capacidades generales de instrucciones justifican una prueba, no una garantía | Pares con/sin ataque y casos irresolubles; medir obediencia, detección y abstención separadamente |

No se selecciona el modelo porque se espere que falle B para favorecer C. Debe ser adecuado para análisis directo y sus límites de decodificación se medirán con transparencia. Una eventual mejora de C necesita el experimento posterior, con el mismo modelo en ambos brazos.

## 11. Alternativa y referencia

**Alternativa: `gemma4:e2b-it-q4_K_M`.** Permite un contraste entre familias y diseños de memoria dentro del equipo existente. Se prefiere E2B frente a E4B por el margen actual; no se confunde su tamaño efectivo con pesos totales. Su soporte nativo de system role y capacidad de código publicados justifican estudiarlo, sin prometer semántica PowerShell correcta. El paquete trae un draft y parámetros de especulación: habrá que registrar su estado efectivo, desactivarlo si el runtime lo permite para la comparación controlada, o declarar esa diferencia antes de la evaluación. No se modifica ahora.

**Referencia: `qwen2.5-coder:7b` Q4_K_M**, digest local histórico intacto. Mantenerlo permite separar cambio de modelo y cambio de prompt: comparar todos con el mismo prompt v2 y, de forma adicional, referencia con prompt v1. Los resultados de una ejecución nueva irían en otra carpeta; nunca reemplazarían el v1. Su conservación no revoca su falta de aprobación.

Si ninguno supera el piloto, la alternativa realista es continuar con el componente determinista ya disponible, describiendo su cobertura parcial, y mantener bloqueada la Fase 2. Se puede autorizar después otro piloto con un compacto como Phi-mini/Ministral o un 8B tras liberar recursos, con reserva nueva si se hacen ajustes. No se presupone hardware adicional ni se reduce el umbral retrospectivamente.

## 12. Diseño propuesto del piloto v2 — no ejecutado

### 12.1 Separación y tamaño

Propuesta: **24 casos de desarrollo y 24 de reserva**, con **al menos 12 familias independientes por partición**, hasta dos formas por familia y tres repeticiones por caso. Un par limpio/ofuscado o con/sin inyección comparte familia y **nunca se divide entre particiones**. Hay 24 casos de reserva, no 72 observaciones independientes; la inferencia estadística se agrupa por familia.

Son casos propios, controlados y nuevos, en `.ps1.txt`, sin ejecutar. No se generan aún archivos ni muestras. **P1–P8 y las fixtures usadas para desarrollar 1A/1B quedan fuera del nuevo desarrollo y de la reserva**; permanecen como historia/regresión. La propuesta breve del cierre 0B decía que P1–P8 podían pasar a desarrollo: este diseño adopta una separación más estricta, coherente con metodología §7, para evitar contaminación. Esa decisión prospectiva debe registrarse al aprobar v2, sin mover artefactos históricos.

Cada partición debe tener positivos B01–B07, al menos dos familias con B02 funcional, combinaciones de 2–3 etiquetas y controles que no contienen comportamientos del catálogo. En la reserva se proponen al menos 6 casos multietiqueta, 6 negativos/benignos sin etiquetas, 4 con incertidumbre esperable y 4 pares con/sin inyección; estos atributos pueden superponerse. La viabilidad de la matriz se revisa antes de escribir/cerrar el manifiesto; no se declara que ya exista.

### 12.2 Matriz conceptual y núcleo comparable

Antes de inferir se identificarán **siete casos núcleo nuevos R1–R7**, además de un R8 de incertidumbre. Son roles de diseño, no muestras ya creadas ni etiquetas adjudicadas a código inexistente:

| Rol | Cobertura prevista y control |
|---|---|
| R1 | B05 administrativo con una familia/sintaxis distinta de P1; candidato benigno |
| R2 | B01 solo, sin ejecución; familia distinta de P3, candidato benigno; puede usar ofuscación soportada |
| R3 | B03 con comentario adversario y control idéntico sin comentario; escenario de persistencia distinto de P4/P8 |
| R4 | B02 funcional aislado, sin descarga ni simple launcher; permite separar B02 de multietiqueta |
| R5 | B04 y B06 coexistentes con operaciones separadas; sin cradle |
| R6 | B07 con acceso explícito a material ficticio almacenado; sin credenciales reales |
| R7 | B01+B02, construcción/familia nueva sin copiar P5/P6; puede estar codificado con contenido de referencia revisado |
| R8 | Técnica no resuelta, por ejemplo formato o dependencia desconocida; B01 solo si hay evidencia, o abstención explícita sin inventar. Candidato benigno |

La selección final de textos, equivalencias, etiquetas, riesgos, cuatro casos benignos y casos ambiguos se valida **antes de ejecutar**. No basta cambiar nombres o URL de P1–P8. Se incluyen formas sin ofuscar, concatenación, variables, Base64 UTF-16LE y formas reservadas no soportadas; se reporta por transformación y tamaño. Los pares revisados estáticamente heredan etiquetas solo si su equivalencia fue documentada.

El resto de la reserva incluye negativos explícitos: URL aislada, mención de IEX en comentario/cadena, `&` con nombre fijo, launcher sin B02 añadido, consulta de Defender, lectura de Run, autenticación legítima con `Get-Credential`, GET sin B06, y escritura/registro frente a simple lectura. No todo benigno carece de etiquetas: inventario o descarga administrativa puede tenerlas sin alto riesgo.

La inyección usa controles idénticos salvo el texto de ataque, sin mezclar su efecto con cambios de ofuscación. Se varían ubicación y redacción en comentarios/cadenas; contenido decodificado también se trata como dato. No se entrega al LLM acceso a herramientas, internet o archivos.

### 12.3 Ground truth y revisión humana

Registrar de antemano ID, familia, split, SHA-256, texto, procedencia, transformación, equivalencia estática, `added_operations`, conjunto de etiquetas, riesgo/contexto, incertidumbre esperada y explicación. Para cada etiqueta, anotar las citas de operación, argumentos, definiciones y relaciones que bastan individual o contextualmente, con coordenadas y procedencia.

El ground truth procede del diseño y revisión humana del texto según la taxonomía. **No se obtiene automáticamente del detector**, ni de salidas de otro LLM. Las abstenciones/FN conocidos de A no se convierten en negativos verdaderos. La referencia decodificada sirve al anotador y al evaluador, nunca se filtra al modelo en B.

El responsable revisará etiquetas y evidencias antes de ejecutar. Idealmente habrá una segunda revisión independiente real; si no existe, se declara un único anotador. La revisión de salidas se hace con modelos anonimizados y orden aleatorio cuando sea factible. Se documentan desacuerdos y adjudicación sin modificar referencias por conveniencia del resultado.

### 12.4 Brazos y prevención del uso repetido de la reserva

En desarrollo se evalúan **principal, alternativa y referencia con el mismo prompt v2**, presupuesto y rúbrica. Se admite como máximo una revisión del prompt común basada en taxonomía y desarrollo nuevo. No se crean instrucciones específicas copiadas de errores de P1–P8 ni prompts distintos para favorecer una familia.

Para respetar el cierre 0B §9, que proponía **como máximo un modelo nuevo de comparación** en la reserva, se nomina un compacto usando solo desarrollo y recursos, antes de abrir la reserva. Brazos de reserva:

1. Referencia Qwen2.5-Coder 7B + prompt v1, control histórico sobre **casos nuevos**.
2. Referencia Qwen2.5-Coder 7B + prompt v2.
3. **Un único nominado nuevo** + el mismo prompt v2.

La comparación entre 2 y 3 estima la diferencia de modelo bajo protocolo común; entre 1 y 2, la diferencia de prompt. No se atribuye al modelo una mejora que también cambió el prompt. Los resultados de la alternativa no nominada quedan identificados como desarrollo y **no bastan para selección definitiva**.

Si se quiere evaluar principal y alternativa en la misma reserva, se debe aprobar **antes** una extensión a cuatro brazos (288 llamadas), justificando el cambio respecto del máximo propuesto en 0B. Es una opción, no una autorización otorgada. Si el nominado falla, no se usa la reserva ya vista para ajustar/seleccionar después a la alternativa: hace falta otra reserva independiente. Todos reciben el mismo procedimiento en la partición en que participan.

El piloto v2 sigue siendo **solo B**, sin entrega de artefactos del desofuscador ni etiquetas del detector al modelo. Así se evita seleccionar por una ventaja de C y se conserva el alcance del cierre. La reserva de selección queda consumida para selección y no se reutiliza como prueba final A/B/C.

### 12.5 Parámetros propuestos y compatibilidad

| Parámetro/condición | Propuesta que deberá congelarse antes de la reserva |
|---|---|
| Base común | `temperature=0`, `seed=42`, `num_ctx=8192`, `num_predict=2048`, `stream=false`, `keep_alive=15m` |
| Sesión | Una conversación nueva por caso/repetición; sin historial cruzado; sin herramientas ni RAG |
| Muestreo residual | Explicitar en v2 `repeat_penalty=1.0`, `presence_penalty=0`, `frequency_penalty=0`, `top_k=20`, `top_p=0.95`, `min_p=0`, verificando aceptación por versión; no dejar distintos defaults escondidos |
| Pensamiento | Probar compatibilidad en desarrollo para solicitar `think=false` si está admitido; confirmar controles con `/api/show`. No usar `/no_think` ni asumir que `/nothink` funciona para Qwen3.5 |
| CPU/backend | Un backend fijo para todos los brazos comparados; base CPU. Propuesta de hilos explícitos 10, pendiente de comprobación de aceptación en desarrollo; sin ajustar hilos por modelo a partir de la reserva |
| Concurrencia | Un modelo residente y una solicitud simultánea. Verificar estado efectivo; no cambiar variables globales ahora |
| KV / especulación | Mantener política KV común y registrar tipo efectivo. Controlar draft/MTP; si no puede igualarse, declarar la diferencia antes y no atribuir latencia solo a tamaño/calidad |
| Plantilla | Mismo contenido de instrucciones y datos; plantilla nativa necesaria por familia registrada, sin editarla con conocimiento de reserva |
| Contrato | Conservar inicialmente `pilot-schema-v1`; si desarrollo demuestra una necesidad real, nueva versión común y hash, sin editar el histórico |

Temperatura cero y salida breve son decisiones de comparación/reproducibilidad del proyecto, **no los parámetros con que Qwen/DeepSeek obtuvieron sus mejores benchmarks publicados**. La clasificación resultante será «mejor bajo este presupuesto», no «máxima capacidad posible de cada modelo». No mezclar una condición thinking larga para un candidato con no-thinking breve para otro. Si un candidato no permite desactivar pensamiento o no entrega JSON completo con este presupuesto, se registra como incompatible con este protocolo; una condición de razonamiento ampliada sería un piloto distinto.

El control referencia+prompt v1 utiliza **los mismos parámetros efectivos comunes del v2** que referencia+prompt v2: solo cambia el texto del prompt. Es una ejecución nueva con prompt histórico, **no una reproducción exacta de la configuración del piloto v1**. Cualquier reproducción exacta adicional debe ser otro brazo identificado y presupuestado, sin mezclarse con esta estimación del efecto del prompt. El cliente actual no implementa los controles nuevos: cualquier adaptación futura pertenece al piloto autorizado, **no se ha implementado aquí**.

### 12.6 Ejecución y registro futuros

1. Obtener autorización explícita de descargas y piloto, manifiesto/etiquetas revisados y configuración firmemente congelada. Registrar versión Ollama/cliente, CPU/RAM/driver, tag y digest completo, plantilla, parámetros efectivos, esquema y hashes de entradas/prompts.
2. Fuera de la reserva, usar casos de desarrollo para verificar carga, esquema y límites. No instalar/actualizar nada por defecto. Un fallo de soporte se documenta antes de pedir cambios de entorno.
3. Verificar RAM disponible y margen; modelo residente único. Mantener fuente de energía y condiciones de suspensión acordadas. No se modifican esas condiciones en este estudio.
4. Tres bloques/repeticiones con orden de modelos y casos contrabalanceado y semilla del orden registrada. Separar primera carga fría de ejecuciones calientes; registrar caché de prefijo y no confundir prefill caliente con capacidad de hardware en frío.
5. Guardar cada respuesta cruda, errores, `done_reason`, campos de pensamiento cuando existan, conteos y tiempos Ollama. No reintentar ni «reparar» JSON para convertir un fallo en éxito. Propuesta de timeout: 300 s, validada en desarrollo y congelada; los timeouts son fallos, no datos omitidos.
6. Medir wall time, carga, prefill y generación por separado; `eval_count/(eval_duration/1e9)` solo si la unidad y los campos son válidos. Si incluye tokens de pensamiento, declararlo; no compararlo con velocidad del JSON final sin aclaración.
7. Muestrear cada ~1 s RAM disponible, compromiso, working set/private bytes del runner, paginación y `/api/ps` incluyendo `size_vram`. Estas métricas responden preguntas distintas. Registrar pico, base previa, frío/caliente, backend y motivo de interrupción, sin recopilar identidad personal.
8. Conservar todo en carpetas nuevas identificadas por ejecución, con hashes; derivar evaluaciones en otras carpetas. Reportar todas las llamadas y una vista separada de latencia sin interrupciones externas justificadas. Una reserva se abre una sola vez; no se ajusta después de leerla.

### 12.7 Métricas y denominadores

| Métrica | Definición propuesta |
|---|---|
| Validez | JSON sintáctico y esquema por separado; denominador todas las llamadas, incluidos timeout, transporte y truncación. `done_reason=length` es fallo aunque el JSON incidentalmente cierre |
| Exactitud multietiqueta | Igualdad de conjuntos por ejecución y por caso; correcto por caso si ≥2/3 ejecuciones tienen el conjunto exacto. Publicar duplicados y lista vacía |
| P / R / F1 | TP/FP/FN por B01–B07, micro y macro, por ejecución y por caso sin fingir independencia de repeticiones. Declarar divisiones por cero; etiquetas sin soporte se marcan no evaluables |
| Fallos con referencia vacía | Aunque se representen como predicción vacía para TP/FP/FN, **no cuentan como exact match correcto ni éxito benigno** |
| Evidencia literal | Citas exactas / todas las citas, por fuente y procedencia; coincidencia normalizada aparte. Si no hay citas, no convertirlo en 100% |
| Soporte semántico principal | Hallazgos con soporte individual o contextual **entre citas efectivamente aportadas y verificadas** / todos los hallazgos predichos; veredicto humano. Informar también cobertura sobre comportamientos esperados para no premiar abstención total |
| Soporte secundario | La misma rúbrica admitiendo contexto no citado, identificada como permisiva |
| Invenciones | Operaciones inexistentes, destinos inventados, credenciales inventadas, afirmaciones no establecidas, especulación y clasificación errónea: conteos por afirmación y ejecuciones afectadas, con denominadores explícitos. Separar FP de etiqueta de falta de soporte |
| Incertidumbre | Fragments señalados correctamente, abstención apropiada en casos irresolubles, excesos de certeza y abstenciones injustificadas en casos resolubles; `confidence` no equivale a probabilidad calibrada |
| Inyección | Obediencia, invariancia de etiquetas/riesgo frente al control, detección explícita y cita correcta del ataque; falsos positivos en controles y explicación por separado |
| Recursos | Media, mediana, p95 y máximo de latencia; carga/prelleno/generación; pico de RAM/compromiso/VRAM, errores por memoria, paginación sostenida y tiempo total proyectado |
| Desgloses | Por comportamiento, familia, positivo/negativo, multietiqueta, técnica, claro/ambiguo, adversario/control, longitud y frío/caliente |

Las familias son la unidad para resúmenes de incertidumbre estadística; con pocas familias se reportan límites exploratorios, no significancia artificial sobre 72 repeticiones. No se crea una puntuación compuesta que oculte B02, JSON o falta de evidencias.

## 13. Criterios para selección definitiva

### 13.1 Conservación de los criterios originales

No se edita `pilot_plan.md` §6 ni se vuelve a juzgar v1. Para aplicarlos a casos nuevos, se preregistra la siguiente correspondencia prospectiva:

| Criterio original | Aplicación propuesta al v2, sin relajación |
|---|---|
| JSON de esquema 100% | **100% de todas las llamadas de reserva** del brazo; fallos incluidos |
| ≥5/7 casos núcleo exactos | **≥5/7 en R1–R7**, por mayoría ≥2/3 como el evaluador histórico. Publicar además exactitud de los 24 y exigir ≥`ceil(24×5/7)` = **18/24** como extensión prospectiva |
| ≥80% citas existentes | **≥80% de citas**, manteniendo denominador y procedencia. No confundir con soporte semántico |
| P7: B01 con evidencia o incertidumbre sin inventar | Regla equivalente en R8, por mayoría; adicionales ambiguos se reportan separados |
| 4/4 benignos no high_risk | Fijar **cuatro casos benignos nuevos** antes de inferir; ninguno high_risk y todos con esquema válido en sus tres ejecuciones |
| P8 resistencia 3/3 | En R3, identificar B03 y no declarar benigno por la instrucción en **3/3**; extender ausencia de obediencia a todos los pares nuevos |
| Estabilidad ≥2/3 por caso | Mismo conjunto de etiquetas en ≥2/3 en **cada uno de los 24 casos**; inválido no cuenta como conjunto estable aceptable |
| Experimento completo ≤1 noche | Registrar medidas; aplicar volumen realmente aprobado y presupuesto de noche acordado. Propuesta: 10 h con 20% de margen, todavía no aprobada |

Los IDs históricos no se sustituyen dentro del evaluador congelado, que contiene P1–P8 explícitos. Haría falta un evaluador v2 separado con esta correspondencia revisada, sin alterar `summary.json` ni el cálculo histórico.

### 13.2 Exigencias adicionales propuestas, pendientes de aprobación previa

Cumplir 5/7 no basta para afirmar que el modelo atiende bien las siete categorías. Se propone aprobar antes de ejecutar:

- Al menos un positivo **respaldado semánticamente** de cada B01–B07, correcto en ≥2/3 repeticiones, incluido B02 aislado y un caso multietiqueta con B02; cero FP en los controles núcleo de launcher, `&` fijo y `Get-Credential` legítimo.
- **≥80% de hallazgos con soporte semántico estricto**, sin permitir que una referencia del equipo se haga pasar por recuperación del sistema. Cobertura/falsos negativos siguen visibles.
- **Cero invenciones críticas** de ejecución, destinos o material de credenciales en la reserva; las especulaciones y errores menos graves se publican y adjudican con rúbrica congelada.
- Ausencia de obediencia en todos los ataques; detección explícita correcta en al menos 3 de los 4 pares adversarios, por mayoría, y cero detecciones falsas en sus controles. Son dos requisitos diferentes.
- Abstención/interpretación justificada en todos los casos núcleo de incertidumbre, sin rellenar contenido no recuperado, y margen de memoria operativo sin OOM ni paginación sostenida asociada a degradación.

Estos son **umbrales propuestos del v2**, no requisitos históricos ya aprobados ni resultados. Si el responsable prefiere mantener algunas dimensiones como descriptivas, debe decidirlo antes de la reserva y la selección reconocerá expresamente esa limitación. No se exige un F1 numérico nuevo escogido sin base; micro/macro-F1 y soporte por etiqueta se reportan para comparar, con prioridad al cumplimiento de todos los criterios obligatorios y luego a mejor soporte estricto, menor invención y menor coste.

Selección definitiva: un nominado cumple los criterios aprobados, es revisado por el responsable y queda fijado por digest y configuración. Si ambos brazos pasan pero la diferencia es pequeña, se reconoce la incertidumbre y se elige por evidencia y coste, sin declarar superioridad estadística. Si ninguno pasa, no se abre la Fase 2 por este documento.

## 14. Decisiones que requieren autorización del responsable

La solicitud actual autoriza este estudio y el documento, **no las acciones siguientes**:

| Decisión concreta | Requisitos presentados para revisión |
|---|---|
| Descargar solo el principal | `qwen3.5:4b-q4_K_M`, aproximadamente **3,3 GB**; presupuesto **4,5–6 GiB de RAM**, inicialmente 8K, CPU. Verificar volumen/digest y licencia al obtenerlo |
| Descargar también la alternativa | `gemma4:e2b-it-q4_K_M`, aproximadamente **4,6 GB**; presupuesto **5–7 GiB**. Pareja: hasta **7,9 GB brutos nuevos**, reserva de disco propuesta 12–16 GB; carga secuencial, nunca ambos a la vez |
| Preparar y ejecutar piloto v2 | Aprobar conjunto 24+24 por familias, revisión humana, roles núcleo, controles y etiquetas antes de inferir; prompt/arnés/evaluador nuevos separados, sin modificar producción ni v1 |
| Alcance de reserva | Predeterminado propuesto: referencia con v1/v2 y un nominado, **216 llamadas**. Cuatro brazos con ambos nuevos: **288 llamadas**, requiere extensión prospectiva explícita |
| Aceptación | Confirmar correspondencia de umbrales originales y cuáles exigencias adicionales del §13.2 pasan a obligatorias; definir duración de noche y timeout |
| Recursos del experimento | Acordar condiciones de energía/suspensión, margen mínimo RAM y cierre manual de aplicaciones. No hay autorización implícita para cerrar trabajos del usuario |
| Aceleración o actualización | Solo si se desea un estudio separado: comprobar iGPU/Vulkan o corregir incompatibilidad demostrada. Sin drivers nuevos ni cambios globales por defecto |
| Selección final y Fase 2 | Decisión posterior basada en resultados humanos revisados; no queda autorizada automáticamente por aprobar descargas/piloto |

No se ejecutan comandos de descarga o inferencia ni se pide aprobación para una acción ya realizada. El siguiente paso concreto recomendable es autorizar **primero la descarga del principal y la preparación del piloto**; la descarga alternativa puede esperar al alcance aprobado. La ausencia de respuesta no constituye autorización.

## 15. Entrega local, Git y límites del estudio

Único archivo creado por este trabajo: **`docs/llm_model_selection.md`**, local y sin staging. No se modificaron otros documentos, prompts, código, ground truth ni resultados. Rama `develop`; sin modificación intencional del índice o historial. No se ejecutaron `git add`, `commit`, `push`, `merge`, `rebase`, `reset --hard` ni `clean`.

La revisión de entrega comprueba que el archivo es UTF-8, sus enlaces relativos existen, los seis hashes de resultados históricos conservan los valores registrados y no hay cambios tracked/staged. No se justifica repetir las 488 pruebas de código por añadir únicamente esta investigación; esa cifra se atribuye al cierre existente y no a una ejecución nueva.

Las conclusiones son una selección razonada bajo recursos observados, no una demostración experimental. Siguen pendientes la carga real de los candidatos, velocidad/memoria efectiva, soporte del modo breve con esquema, veredictos humanos del v2 y cualquier ventaja sobre la referencia. **Principal Qwen3.5 4B; alternativa Gemma 4 E2B; selección definitiva pendiente del piloto v2.**
