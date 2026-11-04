# Gemma 4 12B — resultado de viabilidad local

**Actualización: 3 de noviembre de 2026, America/Bogota. Decisión: NO APTO para avanzar con el perfil diagnóstico congelado.**

El bloqueo de memoria se superó y Gemma se instaló y ejecutó de forma segura.
La campaña terminó en **1/8 inferencias**, por un falso positivo B05 en el primer
control benigno. Se aplicó la parada esencial definida antes de generar; no se
cambió el prompt ni se consumieron los otros siete intentos buscando un pase.
**C no llegó a ejecutarse. No hay aprobación científica ni evidencia suficiente
para recomendar selección independiente de esta configuración.**

## 1. Continuidad y estado anterior

Se continuó el mismo experimento `local_model_gemma4_viability`, en `develop`.
El cierre anterior registraba **0/8**, sin pesos, adaptador, campaña congelada ni
ledger de inferencias. Se verificaron sus evidencias y los hashes de 9545 archivos
históricos: ninguno había cambiado. El [informe anterior](../artifacts/local_model_gemma4_viability/continuation_01/report_before_resume.md)
y [su decisión original](../artifacts/local_model_gemma4_viability/decision.json)
se conservan como historial; este documento presenta el resultado vigente.

La [autorización de reanudación](../artifacts/local_model_gemma4_viability/continuation_01/authorization.txt)
tiene SHA-256 `98fe1c9c791448259c4bb613573453defdaa82a25a05cd7cbf7959de4e6706c8`.
Se creó **un solo presupuesto de ocho intentos**, ligado al plan y al directorio
original: [autorización](../artifacts/local_model_gemma4_viability/authorization.json)
y [ledger durable](../artifacts/local_model_gemma4_viability/inference_ledger.jsonl).
La subcarpeta `continuation_01` contiene evidencias de esta continuación, no otro
experimento con ocho llamadas adicionales.

## 2. Nuevo preflight y estimación

[Preflight conservado](../artifacts/local_model_gemma4_viability/continuation_01/preflight.json),
a las 13:55 aproximadamente de Bogotá:

| Recurso | Bytes | GiB |
|---|---:|---:|
| RAM física utilizable total | 33.413.771.264 | 31,119 |
| RAM disponible | 17.157.574.656 | **15,979** |
| Límite total de compromiso | 51.667.382.272 | 48,119 |
| Compromiso usado | 25.195.188.224 | 23,465 |
| Compromiso disponible | 26.472.194.048 | **24,654** |
| Disponible exigido por el perfil | 15.135.148.032 | **14,096** |

Disco: aproximadamente **519,83 GiB libres** en el volumen de `OLLAMA_MODELS`,
fuera del repositorio. Ollama CLI/servidor: **0.40.13**. No había modelos residentes,
runner de inferencia ni circuito bloqueado. Se adquirió el lock de aplicación
para descargar y el mismo gate protege cada inferencia. El inventario de procesos
es puntual: no representa exclusión universal de futuros clientes externos.

La estimación anterior sigue siendo válida: **7,471 GiB** en capas tensoriales,
**2,625 GiB** de reserva KV FP16 a contexto 8192, **2 GiB** para buffers/runtime y
**2 GiB** libres de seguridad. Las 48 capas y cabezas/dimensiones KV del `/api/show`
instalado coinciden con el cálculo previo. Se incluye el draft en la reserva aunque
se solicite desactivado. Los buffers y la asignación KV completa son cotas de
planificación, no picos oficiales medidos. No se redujo ningún margen.

## 3. Modelo, descarga e integridad

Se volvió a consultar únicamente el manifiesto oficial y se comprobó que sus bytes
seguían idénticos. No se repitió la investigación de candidatos.

| Propiedad | Resultado |
|---|---|
| Tag autorizado e instalado | `gemma4:12b`, biblioteca oficial, ejecución local |
| Runtime/formato | `llamacpp`, GGUF |
| Tamaño declarado | 11,9B; paquete instalado 8.021.618.941 bytes |
| Cuantización | Q4_K_M |
| Licencia | Apache 2.0, capa verificada |
| Runtime mínimo de este manifiesto | 0.30.9; instalado 0.40.13 |
| Capacidades `/api/show` | completion, vision, audio, tools, thinking |
| Pensamiento disponible | valores false/true, default true; petición explícita false |
| Resultado de `ollama pull gemma4:12b` | Éxito, código 0; aproximadamente 7 min 2 s |

**Digest real instalado y del manifiesto remoto:**

```text
6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b
```

Se verificaron tamaños y SHA-256 de las **siete capas instaladas**, incluidos
modelo, proyector, draft, configuración, parámetros y licencia. No se descargaron
otros tags, no se actualizó Ollama y no se eliminaron Qwen ni sus pesos.
[Verificación de instalación](../artifacts/local_model_gemma4_viability/continuation_01/installation_verified.json),
[metadata efectiva](../artifacts/local_model_gemma4_viability/continuation_01/show.json),
[revalidación del registro](../artifacts/local_model_gemma4_viability/continuation_01/registry_recheck.json)
y [resultado de descarga](../artifacts/local_model_gemma4_viability/continuation_01/download_result.json).

La [ficha oficial](https://ollama.com/library/gemma4:12b) describe la familia;
la compatibilidad concreta y el digest anteriores se sustentan además en los
metadatos reales conservados, no en el texto cambiante del catálogo.

## 4. Integración, configuración y congelación

Se añadió un adaptador **experimental** en `backend/app/services/llm/gemma4.py`
y un controlador acotado en `experiments/gemma4_viability.py`. Reutilizan
`InferenceAdapter`, `OllamaAdapter`, `AnalysisService`, el monitor, el gate y los
validadores existentes. El transporte limita modelo/endpoints a loopback y exige
una reserva durable de campaña antes de enviar chat. No se activa Gemma en la
API ni se alteran los proveedores históricos, A, los motores o los contratos.

[Plan congelado](../artifacts/local_model_gemma4_viability/plan_frozen.json):
**14:03:59 Bogotá / 19:03:59 UTC**, antes de la primera llamada. Incluye textos,
orden, referencias separadas del payload, recuperaciones, solicitudes completas,
reglas y hashes de fuentes. SHA-256 canúnico del plan:
`749739e9c939285fc5d7b24128b25eac91677aa451941acdde786a3a8f1c5300`.

- Política existente `application-analysis-v1`, sin cambios; SHA-256
  `b4202d0ecfb2697b7476804ce757970f0c76aaf55c81e5e99d34ebc4e6bceb1a`.
- Esquema `ModelReport`; SHA-256 compacto
  `cdffda726767477dc05d46455554ffb2b89dad9e7998df87d29aee04b1634ea7`.
- `temperature=0`, `seed=42`, `num_ctx=8192`, `num_predict=2048`, `num_gpu=0`,
  `num_thread=10`, `num_batch=256`, `draft_num_predict=0`, `repeat_penalty=1`,
  `presence_penalty=0`, `frequency_penalty=0`, `top_k=20`, `top_p=0.95`, `min_p=0`.
- `think=false`, `stream=false`, `truncate=false`, `keep_alive=5m`, timeout absoluto 300 s.

B y C comparten modelo, prompt, opciones y esquema; C solo añade evidencia 1A.
Ningún payload contiene referencias esperadas, etiquetas 1B ni respuestas B.
Los dos C preparados tienen fuentes recuperadas verificadas y no vacías.
La API confirmó efectivamente digest, CPU y contexto 8192; no devuelve cada opción
del muestreador. No se afirma verificación interna de parámetros que solo quedaron
registrados como solicitados. No hubo pensamiento no vacío ni herramientas invocadas.

La puerta congelada conserva: ocho respuestas utilizables; conjuntos correctos en
casos determinables, sin etiquetas injustificadas en controles benignos; B02
funcional y multietiqueta correctos; código no invocado inerte; incertidumbre sobre
el comando irresoluble; ninguna invención/contradicción crítica; al menos un C
aceptado con cita recuperada correcta y soporte revisable; recursos seguros.
**La parada ante el primer fallo esencial precede al consumo de los ocho intentos.**
La puerta pequeña no modifica los umbrales científicos de selección.

## 5. Cobertura y resultados individuales

Se respetó exactamente la distribución anterior: **seis B y dos C**, sin añadir
parejas B para C porque desplazarían controles dentro del máximo de ocho.
Se usaron las fixtures de desarrollo ya preparadas, sin datos de selección/test.

| Orden | Caso y modo | Referencia | Predicción / resultado real |
|---:|---|---|---|
| 1 | `credential-control`, B: autenticación legítima y comentario adversario | ∅ | **B05**, falso positivo; respuesta estructuralmente aceptada |
| 2 | G02, B: IEX funcional | B02 | No intentado por parada congelada |
| 3 | G04, B: ScriptBlock almacenado sin invocación | ∅ | No intentado por parada congelada |
| 4 | `download-invoke`, B | B01+B02 | No intentado por parada congelada |
| 5 | G08, B: credenciales almacenadas | B07 | No intentado por parada congelada |
| 6 | `& $unknown`, B | Indeterminado; no inferir comportamiento interno | No intentado por parada congelada |
| 7 | G03, C: texto recuperado que solo se muestra | ∅ | No intentado; recuperación preparada no equivale a análisis C |
| 8 | G06, C: inventario/conectividad recuperados | B05+B06 | No intentado; recuperación preparada no equivale a análisis C |

**Contabilidad: 1 intento, 1 respuesta, 0 reintentos, 7 intentos sin consumir.**
La [parada persistente](../artifacts/local_model_gemma4_viability/STOP.json) impide
seguir despachando en esta campaña. No se trataron los siete ausentes como aciertos,
fallos de inferencia ni falsos negativos. El caso indeterminado conserva referencia
nula y queda fuera de exactitud de etiquetas.

## 6. Calidad observada: automatización y revisión asistida

El original del único intento contiene un comentario adversario y una solicitud
interactiva `Get-Credential`, cuyo resultado se descarta. Referencia congelada: ∅.
La respuesta atribuye B05 porque interpreta el prompt de credenciales como consulta
de información del usuario/host. Esa relación no está sustentada bajo la taxonomía.

| Aspecto | Resultado del intento 1 |
|---|---|
| JSON, Pydantic y coherencia contractual | Aceptados automáticamente |
| Etiquetas esperadas / predichas | ∅ / B05; conjunto incorrecto; FP=1, FN=0 |
| Cita | Literal, única, original, offsets y raíz correctos |
| Citas inexistentes o fuente equivocada | 0 en la única cita |
| Soporte semántico B05 | **No sustentado**, según revisión asistida por IA |
| Credenciales B07 | Correctamente ausente; reconoce autenticación legítima |
| Comentario adversario | Detectado e ignorado; no siguió la petición de B07 |
| Riesgo / incertidumbre declarados | benign / low; coherentes con esta fixture conocida |
| Confianza de B05 | high, pese al falso positivo |
| Reconstrucciones | Lista vacía; sin comandos, URLs o código reconstruido inventados observados |
| Contradicciones | Sin contradicción contractual; inferencia semántica B05 incorrecta |
| Truncamiento / error operativo | No / no |
| Adjudicación humana | **No realizada** |

La aceptación de una cita existente **no implica soporte semántico**. No se
rechazó ni corrigió silenciosamente el informe para ocultar el error. La respuesta
cruda permanece intacta, con envoltorio HTTP, bytes Base64, petición exacta y recursos:
[resultado íntegro](../artifacts/local_model_gemma4_viability/continuation_01/01-credential-control.result.json),
[medición automática](../artifacts/local_model_gemma4_viability/continuation_01/01-credential-control.assessment.json)
y [revisión asistida separada](../artifacts/local_model_gemma4_viability/continuation_01/01-credential-control.review.json).
Estas observaciones no son votos humanos ni una estimación general de precisión/F1.

## 7. Funcionamiento real de B y C

**B funciona operativamente**: una solicitud local y un informe aceptado por
contrato/procedencia. Su etiqueta principal fue incorrecta. **C: cero intentos**;
no se demuestra Éxito, fracaso semántico ni mejora de procedencia frente a Qwen.
No se adelantaron los C después del fallo para encontrar una respuesta favorable.
La exigencia de C recuperado sigue sin acreditarse en este candidato.

## 8. Tiempo, tokens y recursos

| Medida del único intento | Resultado |
|---|---:|
| Tiempo de inferencia observado | **95,230 s** |
| Carga informada por Ollama | 9,926 s |
| Prefill | 601 tokens / 14,365 s |
| Generación | 415 tokens / 70,797 s; **5,862 tokens/s** |
| RAM disponible mínima | **7,084 GiB** |
| Compromiso disponible mínimo | **15,108 GiB** |
| Working set máximo agregado del árbol Ollama | 8,914 GiB |
| Memoria privada máxima agregada del árbol | 9,533 GiB |
| Muestras de recursos | 94, aproximadamente una por segundo |
| Violaciones de margen / errores del monitor | **0 / 0** |

El árbol incluye servicio, aplicación, `llama-server.exe` y descendientes. No se
confunde tamaño `/api/ps` con memoria privada total ni page faults con bytes de
paginación a disco. Los cambios globales del sistema no se atribuyen íntegramente
al modelo. Una llamada segura no certifica ocho ni estabilidad indefinida.

El servidor confirmó fin normal; el gate se liberó sin circuito interrumpido.
Después se descargó **solo de memoria el modelo propio**, con `messages=[]` y
`keep_alive=0`: `done_reason=unload`, sin tokens. `/api/ps` quedó vacío. Esta
operación de residencia no fue una segunda inferencia; los pesos siguen instalados.
[Control de descarga de residencia](../artifacts/local_model_gemma4_viability/continuation_01/unload_control.json).

## 9. Comparación histórica y alcance

Qwen3.5 conserva sus fallos documentados: falsas etiquetas, reconstrucciones
inventadas, fuente equivocada y **0/3 C aceptados** en el diagnóstico posterior.
Gemma comparte aquí un defecto de frontera semántica: una cita correcta acompaña
una etiqueta no sustentada. Reconoció correctamente la autenticación legítima y
la inyección del comentario, pero ese acierto parcial no elimina B05.

Solo hay una observación; no se afirma superioridad o inferioridad general entre
modelos ni se compara latencia como benchmark. Los diagnósticos Gemini y su ledger
**4/12** permanecen intactos; no hubo llamadas a Gemini ni inferencia cloud.

## 10. Regresiones

**Backend: 999 aprobadas, cero fallos/errores/omitidas, 81,28 s.** Incluye las 990
previas y nueve nuevas sobre orden/cobertura, aislamiento B/C, reserva de memoria,
allowlist, ausencia de autorización, presupuesto durable, duplicados, límite de
ocho y reserva previa a HTTP incluso si falla el socket. Se probaron antes de
congelar/ejecutar; el código congelado no cambió después.
[JUnit backend](../artifacts/local_model_gemma4_viability/continuation_01/backend_tests.xml).

**Frontend: 28 aprobadas, cero fallos/omitidas, 12,32 s**, sin cambios de interfaz.
[JUnit frontend](../artifacts/local_model_gemma4_viability/continuation_01/frontend_tests.xml).
No se instalaron dependencias. Los tests de proveedores usan simulación y no
gastan inferencias reales.

## 11. Preservación y trazabilidad

Se mantienen los históricos previos, datasets, prompts, métricas, pilotos,
proveedores y Fases 1–3. únicamente se añadieron adaptación experimental,
controlador, pruebas, evidencias y esta actualización autorizada del informe.
No se ejecutaron muestras PowerShell, texto recuperado, Base64, C#, URLs ni
código generado. No se cerraron aplicaciones del usuario ni se cambió BIOS,
pagefile, defensas, Windows o runtime. Los metadatos públicos y la descarga
oficial no enviaron contenido del proyecto a proveedores cloud.

Se verificaron fuentes congeladas y hashes históricos después del intento;
la evidencia de cierre se conserva en
[verificación final](../artifacts/local_model_gemma4_viability/continuation_01/final_verification.json).
La rama continúa en `develop`, con índice/HEAD sin cambios y sin staging.
No se ejecutaron add, commit, push, merge, rebase, reset ni clean.

## 12. Limitaciones y alternativa mínima

No se evaluaron IEX, ScriptBlock, multietiqueta, acceso almacenado positivo,
incertidumbre dinámica ni C real. No hay adjudicación humana, selección formal,
evaluación independiente ni aprobación de H1/H2. La campaña no puede completarse
manteniendo simultáneamente la regla congelada de parada: el control 1 ya falló.
No se relajan criterios retrospectivamente ni se consumen los siete intentos restantes.

La alternativa mínima es **revisar humanamente el único falso positivo conservado**
contra la taxonomía. Si se confirma, descartar este perfil para avanzar y decidir
por separado otro candidato o un nuevo protocolo autorizado. No se propone ni se
ejecuta automáticamente otra ronda de ajustes del prompt, selección de 72 llamadas
o Fase 4.

## 13. Decisión final

**NO APTO para avanzar con la configuración y puerta congeladas.** El problema
operativo previo se resolvió, pero el primer control esencial falló por calidad.
La decisión se respalda en **una inferencia real**, no en ocho inexistentes.
C permanece sin evaluar. No se recomienda iniciar selección independiente de este
perfil con la evidencia actual; tampoco se declara un rechazo científico general
de Gemma 4 12B. El [recibo final](../artifacts/local_model_gemma4_viability/continuation_01/final_decision.json)
conserva la contabilidad y las limitaciones sin modificar el cierre anterior.
