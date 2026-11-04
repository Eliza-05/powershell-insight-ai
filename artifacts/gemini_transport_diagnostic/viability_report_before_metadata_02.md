# Viabilidad experimental de Gemini — 2 de noviembre de 2026

Continuación: [diagnóstico y corrección del transporte](gemini_transport_diagnostic.md).
Se corrigió un defecto local reproducible de doble descompresión, sin nuevas llamadas
a la API. El presupuesto permanece en 1/12 y 0 inferencias. La segunda consulta requiere
autorización expresa; su plan prospectivo reserva como máximo diez generaciones.

**Resultado: integración implementada; viabilidad del servicio y calidad pendientes.**
La primera consulta de metadatos terminó con `gemini_transport_error`. Se detuvo el
experimento sin reintentar: **1/12 solicitudes contabilizadas, 0 inferencias de las
11 previstas**. No se obtuvo un listado validado de modelos ni una respuesta del
modelo. No se concluye que la clave sea inválida ni se atribuye calidad a Gemini.

## Credenciales y nivel gratuito

Se verificó que `.env` existe en la raíz, está ignorado y no está versionado. La clave
se lee exclusivamente en Python desde `GEMINI_API_KEY` del proceso o, si falta, mediante
`dotenv_values` del archivo raíz. No hay interpolación ni exportación de otras variables
del archivo. La precedencia corresponde al entorno del proceso. La ruta se calcula
desde el módulo y no depende del directorio de trabajo.

Se inicializa `google.genai.Client` con esa variable explícita, Developer API, URL HTTPS
fija, SDK `google-genai==2.34.0` y `python-dotenv==1.2.4`. No se usa `GOOGLE_API_KEY` como
alternativa, Vertex AI, proxies del entorno ni URLs configurables. No se muestra,
documenta, exporta al frontend ni registra la clave o partes de ella. Los errores
publicados contienen únicamente categorías; los cuerpos de errores HTTP se descartan.
Una respuesta que repita la credencial, incluso escapada en JSON, se rechaza antes de
conservar su contenido. Los logs del SDK/HTTP no se propagan.

El propietario confirmó en el chat que AI Studio muestra **nivel gratuito**. El acceso
automatizado al navegador falló, por lo que no se inspeccionó el panel de facturación
ni los límites específicos del proyecto. No se confirmó cuota positiva por modelo:
RPM, TPM, RPD, uso actual y saldo restante siguen **desconocidos**. La consulta de
modelos, aunque hubiera funcionado, no demostraría cuota gratuita de inferencia.
Véanse [confirmación](../artifacts/gemini_viability/owner_confirmation.json) y
[error](../artifacts/gemini_viability/preflight_error.json).

No se habilitó facturación, no se consultaron operaciones de pago y no se enviaron
solicitudes de generación. El ledger cuenta conservadoramente el intento de metadatos
aunque no se pudo verificar su recepción remota. No equivale al contador del proveedor.
El intento inicial no conservó subtipo de excepción ni estado HTTP; no se inventan.

## Verificación documental oficial

Consulta documental: 2026-11-02, America/Bogota. La documentación pública y los permisos
de una clave concreta son evidencias distintas.

| Aspecto | Verificación y efecto en el experimento |
|---|---|
| Modelo preferido | Google publica `gemini-3.8-flash`, con entrada/salida de texto gratuitas en Free Tier. Su disponibilidad con esta clave no pudo verificarse. [Modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [precios](https://ai.google.dev/gemini-api/docs/pricing). |
| Alternativa | `gemini-2.5-flash` tiene entrada/salida de texto gratuitas documentadas. Solo se elegiría si el listado validado no contiene 3.8 y sí contiene 2.5; la decisión se guardaría antes de inferir. No se probó ni se seleccionó esa alternativa. [Precios](https://ai.google.dev/gemini-api/docs/pricing#gemini-2.5-flash). |
| Cuotas | Son por proyecto; se controlan solicitudes por minuto/día y tokens de entrada por minuto. Los límites efectivos se consultan en AI Studio; RPD reinicia a medianoche del Pacífico. No se copian cifras de otros proyectos. [Cuotas](https://ai.google.dev/gemini-api/docs/rate-limits). |
| JSON | Se admite un subconjunto de JSON Schema. Algunas restricciones, como longitud de cadenas, se ignoran en el servidor; permanecen exigidas por Pydantic y los validadores locales. JSON correcto no certifica etiquetas ni semántica. [Respuestas estructuradas](https://ai.google.dev/gemini-api/docs/structured-output). |
| Razonamiento | 3.8 admite low/medium/high; minimal produce error. Se prepara low, sin devolver pensamientos. Para 2.5 se prepara un presupuesto de 512 tokens. Son configuraciones prospectivas, no observaciones. [Modelo](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash), [thinking](https://ai.google.dev/gemini-api/docs/thinking). |
| Privacidad | En servicios gratuitos Google puede usar entradas/salidas para mejorar productos y permitir revisión humana. Por ello se admiten exclusivamente los textos sintéticos fijados; nunca scripts privados, secretos ni datos personales. [Términos](https://ai.google.dev/gemini-api/terms#data-use-unpaid). |
| Ciberseguridad | La política prohíbe facilitar malware, abuso de infraestructura o evasión de protecciones, y contempla consideraciones educativas/científicas. Este trabajo es clasificación estática de muestras académicas; no se rebajan filtros ni se intenta eludir bloqueos. [Política](https://policies.google.com/terms/generative-ai/use-policy). |

El listado utiliza una sola página de hasta 1000 modelos mediante el SDK oficial.
Si hay páginas adicionales, se informa sin consultarlas automáticamente. No se usa
`countTokens`, búsqueda, herramientas, archivos, caché explícita, Batch ni URL context.
[Referencia Models](https://ai.google.dev/api/models), [SDK oficial](https://googleapis.github.io/python-genai/).

## Integración y seguridad de A/B/C

`services/pipelines/provider.py` define la interfaz común y el esquema de respuesta.
Ollama conserva sus importaciones compatibles y su comportamiento. `AnalysisService`
acepta `GeminiAdapter` por inyección; su selección no exige reescribir los pipelines:

- **A:** solo 1A + 1B locales; no consulta Gemini ni Ollama.
- **B:** política compartida y texto original.
- **C:** misma política, modelo y parámetros que B, más recuperación verificada de 1A.

`build_context` sigue siendo el constructor común. Nunca se envían resultados de 1B,
etiquetas esperadas, criterios de evaluación ni respuestas de otros casos. La salida
usa `ModelReport`, JSON estricto y comprobaciones de literalidad, unicidad, coordenadas
y procedencia. La reconstrucción declarada por el modelo no se admite como evidencia
verificada. No se certifica automáticamente soporte semántico.

El adaptador exige hashes de los originales sintéticos permitidos. El transporte
también comprueba esa lista y bloquea herramientas. Solo admite el host de Google,
GET del listado y POST de generación al modelo elegido; rechaza redirecciones. Las
URLs `.example.invalid` de las muestras son texto, nunca destinos consultados.

Cada intento HTTP se reserva y sincroniza en `requests.jsonl` **antes** de contactar
la red. Se incluyen metadatos, fallos y timeouts dentro del límite total de 12. El
SDK usa un solo intento; HTTP no reintenta conexiones. Se rechazan solicitudes
duplicadas y un segundo listado. Reiniciar Python no reinicia el presupuesto. Un
diario corrupto o lock pendiente bloquea el envío. No borrar ni sustituir ese diario.

Una confirmación explícita y reciente de nivel Free debe corresponder al modelo; no
se fabrica con el éxito del listado. El controlador preparado espacia inferencias
al menos 61 segundos, conserva los límites desconocidos y detiene la campaña ante
errores. La cadencia no demuestra que exista cuota. Si se conocen TPM/RPD, se aplican
comprobaciones conservadoras adicionales. La confirmación caduca en una hora.

Parámetros prospectivos: temperatura 1, seed 42, top_p 0,95, un candidato y máximo
4096 tokens totales de salida, incluidos tokens de pensamiento. La política solicita
una respuesta final de hasta 2048 tokens. No se promete determinismo del servicio ni
igualdad del presupuesto de razonamiento con Qwen.

## Casos y resultados

El plan reserva 1 consulta de modelos + 9 B + 2 C = **12 solicitudes máximas**.
Las dos C aparecen temprano para comprobar recuperación si la cuota lo permite.
Todos los textos se definieron en `experiments/gemini_cases.py`; no se leyeron los
conjuntos reservados para construirlos. No se ejecutó ningún texto PowerShell.

La revisión local corrigió G01: consultar preferencias de defensa es B05, aunque
no es B04 ni B07. Se conserva `plan.json` original y se activa `plan_r1.json`, con
una enmienda trazable realizada **antes de toda inferencia**. No hubo salida de
Gemini con la que ajustar etiquetas o parámetros.

| Caso | Criterio esperado B/C | Resultado de A local | Gemini |
|---|---|---|---|
| G01: Write-Output, autenticación interactiva y consulta de defensas | B05 por la consulta; sin B04/B07 | B05, completo | B no ejecutado |
| G02: IEX con entrada vinculada | B02 | B02, completo | B no ejecutado |
| G03: Base64 que se decodifica y muestra sin invocarse | Ninguna etiqueta; sin B02 | Sin etiquetas; 3 textos recuperados verificados | B/C no ejecutados |
| G04: bloque almacenado, nunca invocado | Ninguna etiqueta | Sin etiquetas, parcial | B no ejecutado |
| G05: descarga desde dominio ficticio | B01; sin inventar ejecución | B01, completo | B no ejecutado |
| G06: EncodedCommand con inventario + conectividad | B05+B06; sin B02 automático | B05+B06; 1 recuperación verificada | B/C no ejecutados |
| G07: modificación que debilita defensas | B04 | B04, parcial | B no ejecutado |
| G08: acceso a entrada ficticia de almacén de credenciales | B07 | B07, completo | B no ejecutado |
| G09: IEX con entrada desconocida y comentario adversario | B02 externo, incertidumbre e inyección detectada | Sin etiquetas, parcial; limitación del subconjunto 1B | B no ejecutado |

Se completaron 9 análisis A locales. G03/G06 tienen recuperación C **preparada**, sin
demostrar que Gemini la interprete o cite correctamente. G01 agrupa tres operaciones
benignas para acomodar el presupuesto; no permite estimar sus efectos aisladamente.

JSON válido, etiquetas, multietiqueta, evidencia, procedencia, soporte semántico,
invenciones, incertidumbre, resistencia a inyección y éxito de C quedan **no evaluados
para Gemini**, no puntuados como cero aciertos. Tampoco existen latencias de inferencia
ni contadores de tokens de generación. El consumo de generación de este experimento
es cero. Se preparó su captura para futuras respuestas exitosas, incluida versión
exacta, cuerpo JSON crudo, uso y latencia. No hay respuesta cruda del modelo que entregar.

## Comparación y decisión

Los resultados previos de Qwen3.5 registran fallos semánticos y de contrato, perfiles
de desarrollo agotados y un piloto v2 cerrado sin aprobación. Se conservan como
históricos en [el cierre anterior](pre_phase4_model_readiness.md); no se ejecutó Ollama
durante este experimento. Qwen3.5 es un candidato provisional, no un modelo seleccionado
científicamente. Esta entrega tampoco aprueba Gemini.

No se puede afirmar que Gemini mejore calidad o latencia: tiene **cero inferencias**
observadas y estos casos/configuración no son la selección histórica de Qwen. El
servicio remoto también cambia privacidad, disponibilidad de red, cuotas y control
de versiones. Los resultados A y las respuestas simuladas de los tests no son
resultados de Gemini.

**Recomendación:** conservar el adaptador experimental; no migrar aún el proveedor
principal. Primero hay que resolver la conectividad, verificar autenticación/listado,
confirmar cuota positiva del modelo en el proyecto y autorizar expresamente cualquier
nuevo intento del preflight fallido. No se harán reintentos silenciosos ni se ampliará
el máximo de 12. Quedan 11 reservas sin usar, no 12 nuevas.

Una selección futura requiere un protocolo independiente autorizado, criterios,
prompt/modelo/parámetros congelados, casos separados del desarrollo, adjudicación
semántica humana y una decisión expresa del responsable. No se inició Fase 4 ni
la selección completa de 72 llamadas.

## Uso preparado y migración posterior

Instalación opcional, desde raíz:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-gemini.txt
```

El controlador es `python -m experiments.gemini_viability`, con acciones `prepare`,
`preflight` y `run --free-tier-confirmation RUTA_JSON`. **No repetirlas en el estado
actual:** los artefactos son de creación exclusiva y el preflight ya fue intentado.
No se genera un archivo habilitante a partir de la confirmación genérica del chat.

El JSON habilitante, una vez verificados proyecto/modelo y autorizado el nuevo intento,
se corresponde con `FreeTierConfirmation`: `model`, `confirmed_at` UTC, `source` igual a
`owner_ai_studio_confirmation`, `tier` igual a `Free` y límites conocidos o null. Es una
declaración del responsable, no prueba obtenida por una API. No incluye credenciales.

`experiments/gemini_application.py` prepara una fábrica FastAPI separada. Requiere
preflight exitoso, decisión de modelo y `PSI_GEMINI_FREE_TIER_CONFIRMATION` apuntando al
JSON habilitante. Comparte exactamente el ledger de 12 solicitudes y la lista sintética.
Con el bloqueo actual se niega a arrancar. No se ejecutó esta aplicación remota.

Una vez satisfechos esos requisitos, el comando preparado sería:

```powershell
$env:PSI_GEMINI_FREE_TIER_CONFIRMATION = 'RUTA_AL_JSON_VERIFICADO'
.\.venv\Scripts\python.exe -B -m uvicorn experiments.gemini_application:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

React conserva `/api` relativo y no recibe la clave. La API informa proveedor/modelo
reales al inyectar Gemini y ofrece `/api/provider/status`; mantiene `/api/ollama/status`
como alias compatible. Las consultas de estado de Gemini son locales y no consumen
solicitudes. `app.main` y el frontend siguen con su configuración previa.

Para convertirlo posteriormente en principal: aprobar el candidato, seleccionar
proveedor en la fábrica de la aplicación, actualizar rótulos Ollama/Qwen y estado de
recursos en React, diseñar admisión de datos adecuada a la privacidad del nivel elegido
y sustituir el presupuesto diagnóstico por un control de cuotas autorizado. La lista
sintética no se retira durante este experimento. Se mantienen A/B/C separados y se
conserva Ollama histórico. No descargar modelos ni habilitar facturación para continuar.

## Archivos y validación

Nuevos: `backend/requirements-gemini.txt`, `services/pipelines/provider.py`,
`services/llm/gemini.py`, `gemini_credentials.py`, `gemini_budget.py`,
`backend/tests/pipelines/test_gemini.py`, `experiments/gemini_cases.py`,
`gemini_viability.py`, `gemini_application.py`, `gemini_audit.py`, `gemini_closeout.py`,
este informe y `artifacts/gemini_viability/`.

Ediciones de esta tarea: `.env.example`, `README.md`,
`backend/app/services/pipelines/ollama.py`, `service.py` y `backend/app/api/application.py`.
Se conservaron cambios locales anteriores y archivos históricos; `.gitignore` ya
protegía `.env` y no necesitó cambios. No se modificó `.env`.

La primera regresión pasó 928 pruebas. Se añadieron controles adicionales; una
ejecución intermedia detectó que el auditor local invocaba Git desde Python, prohibido
por el contrato estático del repositorio. Se corrigió separando los chequeos Git de
la exploración Python, sin debilitar ese test. La evidencia final se registra en
[`validation.json`](../artifacts/gemini_viability/validation.json) y el JUnit backend.
La ejecución final pasó **932 pruebas backend**, incluidas 24 nuevas del adaptador.
Las **28 pruebas frontend** y el build TypeScript/Vite pasaron. Una advertencia conocida
Starlette/httpx no afecta el resultado.

La auditoría final busca la credencial en archivos del proyecto y `frontend/dist`
sin mostrar su valor. [Artefactos y resumen](../artifacts/gemini_viability/summary.json).
Los resultados del piloto v2 y Qwen permanecen separados. Trabajo local en `develop`,
sin staging, commit, push, merge, rebase ni operaciones Git de escritura.
