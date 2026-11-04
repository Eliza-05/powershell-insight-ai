# Viabilidad experimental de Gemini 3.6 Flash

**Resultado: una generación nueva intentada; HTTP 400 y parada sin reintentos.**
G03-B recibió `gemini_invalid_request` en **5,650 segundos**. G03-C, G06-B y G06-C
no se enviaron. No hubo salida del modelo que permita evaluar calidad o recorrido C.
El rechazo remoto deja **pendiente la compatibilidad efectiva de esta petición**;
las pruebas locales de SDK y serialización no la certifican.

**Ledger global: 4/12 reservas utilizadas; ocho sin utilizar.** Se conservaron los
dos metadatos y la generación 3.8 fallida con HTTP 503. El ensayo de 3.6 es un nuevo
experimento, no una sustitución ni una repetición de aquella petición al mismo modelo.

## Elección y verificación sin nuevos metadatos

El cambio de candidato fue autorizado expresamente por el propietario para observar
disponibilidad y utilidad semántica. El listado autenticado de 60 modelos ya guardado
contiene `models/gemini-3.6-flash`, anuncia `generateContent` y thinking, y devuelve
`version=3.6-flash-07-2026`. Ese campo procede del listado anterior; **no es una versión
efectiva de generación observada en este ensayo**. No se llamó a `models.list` otra vez.

Google documenta 3.6 como versión estable de una generación previa de Flash, aún
disponible para producción, con salida estructurada. Eso justifica investigar el
candidato y no demuestra su disponibilidad o calidad con este proyecto.
[Ficha oficial](https://ai.google.dev/gemini-api/docs/models/gemini-3.6-flash).

El propietario informó Free tier, facturación no activada, proyecto Default Gemini
Project y límites 5 RPM, 250.000 TPM y 20 RPD para 3.6. No informó un nuevo saldo
instantáneo ni se consultó el panel automáticamente. La documentación publica entrada
y salida gratuitas para Standard en Free Tier; se mantuvieron herramientas deshabilitadas.
[Precios oficiales](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.6-flash).

Antes de modificar el adaptador se verificaron los hashes del cierre r2 y el ledger
de tres entradas. Se inventariaron todos los artefactos anteriores y se conservó
una copia del adaptador previo en
[`legacy_gemini_adapter_before36.py.txt`](../artifacts/gemini_36/legacy_gemini_adapter_before36.py.txt).
No se cambiaron `.env`, claves, facturación, planes r2 ni expectativas de desarrollo.

## Configuración exacta y compatibilidad

Se mantuvo `google-genai==2.34.0` y el endpoint Developer API `generateContent`.
La configuración 3.6 tiene clase propia, selección explícita y ningún fallback.
El adaptador común únicamente extrajo su construcción de configuración a un método
sobrescribible; los tests verifican que la configuración histórica no cambió.

| Campo | Solicitud congelada antes de la respuesta |
|---|---|
| Modelo | `gemini-3.6-flash` |
| Razonamiento | `thinking_level=medium`, `include_thoughts=false` |
| Salida y pensamiento | `max_output_tokens=8192` en total |
| Política de respuesta final | La política común existente sigue solicitando hasta 2048 tokens de JSON final |
| Formato | `application/json` con el mismo JSON Schema de aplicación |
| Timeout | 60 s |
| Herramientas | Lista vacía; automatic function calling deshabilitado |
| Transporte | HTTPS fijo, certificados verificados, sin redirects ni proxies heredados |
| Reintentos | Un intento SDK y cero reintentos HTTP |
| Muestreo | `temperature`, `top_p`, `top_k`, `seed`, `candidate_count` y penalizaciones omitidos |

La guía de migración indica retirar los parámetros de muestreo ignorados y el número
de candidatos no soportado. Se omitió también seed para no atribuirle un efecto no
confirmado. No se enviaron turnos de modelo precargados. La política y el esquema
permanecen comunes a B/C.
[Cambios oficiales de parámetros](https://aistudio.google.com/docs/whats-new-gemini-3.6).

`medium` está documentado entre los niveles compatibles de 3.6. Se eligió un límite
total de 8192 para alojar pensamiento y respuesta final; no se fijó un presupuesto
numérico de pensamiento distinto. No se presupone que el máximo de salida sea un
consumo real o que el nivel solicitado sea confirmado internamente.
[Thinking](https://ai.google.dev/gemini-api/docs/thinking).

El SDK instalado construyó y serializó la petición en tests sin red. En esta versión,
el objeto HTTP usa `thinkingConfig` con campos internos `thinking_level` e
`include_thoughts`; se verificó la serialización que produce el SDK, sin afirmar una
aceptación del proveedor por ese hecho. El servicio devolvió **HTTP 400**: no se
confirmaron los parámetros efectivos, la versión de generación ni el formato de salida.
El motivo específico del argumento rechazado no se conservó y no se atribuye a un
campo concreto, al esquema o al modelo sin evidencia adicional.

Los límites internos de Pydantic y la validación literal siguen aplicándose localmente.
Que un proveedor admita JSON estructurado no garantiza cada esquema o interpretación.
[Salida estructurada](https://ai.google.dev/gemini-api/docs/structured-output).

## Plan y autorización congelados

El nuevo [`plan_v1.json`](../artifacts/gemini_36/plan_v1.json) contiene exactamente
G03-B, G03-C, G06-B y G06-C. Sus scripts y etiquetas esperadas se copiaron sin cambios
de los cuatro primeros casos del plan r2. El plan r2 de 3.8 no se sobrescribió.

La [autorización registrada](../artifacts/gemini_36/authorization.json) permite hasta
cuatro solicitudes nuevas y está ligada al [binding](../artifacts/gemini_36/binding.json),
que congela modelo, parámetros, política, esquema, contextos, código y hash inicial
del ledger. Se comprueban esos hashes antes de cada envío. No se editaron después de
observar la respuesta. El intento persistente bloquea reinicios y reejecuciones silenciosas.

Se usa el mismo `RequestBudget` y su archivo existente, reservando y sincronizando
antes de la red. El controlador solo admite iniciar con tres entradas y como máximo
terminar con siete. Establece al menos 21 segundos entre inicios y controla una ventana
conservadora de 61 s; la mayor reserva estimada preparada es **15.237 tokens**,
incluida la salida máxima, inferior a 250.000 TPM. Solo se envió una solicitud, así
que no hubo intervalo real entre dos generaciones que medir.

La confirmación Free del propietario se registró antes de ejecutar. El saldo RPD
restante se conservó como desconocido, no como 20 solicitudes libres. Un 429, 503,
401, 403 u otro fallo operativo detiene el lote. Un rechazo exclusivamente estructural
con respuesta de modelo conservada podría permitir analizar el caso siguiente sin
repetir el anterior; esa política se fijó antes del ensayo.

## Resultados operativos por solicitud

| Orden | Caso | Expectativa congelada | Resultado real |
|---|---|---|---|
| 1 | G03-B | Ninguna etiqueta; decodificar y mostrar no es ejecución dinámica | Intentado: HTTP 400, `gemini_invalid_request` |
| 2 | G03-C | Misma muestra y expectativa, con recuperación verificada de 1A | No ejecutado tras la parada |
| 3 | G06-B | B05 + B06; no inferir B02 por EncodedCommand | No ejecutado |
| 4 | G06-C | B05 + B06 con recuperación verificada de 1A | No ejecutado |

La reserva global **4** se inició a **2026-11-03 03:01:28.118455 UTC**
(2 de noviembre, 22:01:28, America/Bogota). Latencia del adaptador: **5,6503203 s**.
Run ID: `10bac60b-62b2-451c-a78b-436fe80a371e`.
No se recibieron response ID del proveedor, finish reason, versión efectiva o contadores
de tokens. El modelo solicitado y los metadatos históricos disponibles sí están registrados.

Se conservaron la petición exacta, configuración, hashes, tiempos, contador, estado
HTTP y categoría en [`G03_B.json`](../artifacts/gemini_36/G03_B.json). El transporte
previo descarta cuerpos de errores HTTP potencialmente sensibles; el cuerpo del 400
no está disponible. No hay una respuesta cruda del modelo que entregar ni se fabrican
mensajes para justificar el rechazo. Esta limitación impide identificar aquí el
argumento rechazado. No se hizo otra llamada para recuperarlo.

El resultado fue HTTP 400, no un nuevo 503. No permite afirmar que 3.6 tenga mayor
disponibilidad que 3.8 ni que todos los modelos Gemini estén indisponibles. El rechazo
de una petición tampoco es evidencia de clasificación semántica incorrecta.

## Calidad, B/C y procedencia

**G03 y G06: calidad no evaluable en este ensayo.** No existen predicciones observadas
de B01–B07, citas, reconstrucciones, incertidumbre o riesgo del modelo. No se computa
exactitud 0/4 ni se asignan falsos positivos a los casos no ejecutados. Los flags
genéricos de estructura o igualdad en falso reflejan ausencia de salida aceptada;
no una predicción observada. El riesgo `unknown` del resultado fallido pertenece al
pipeline, no a una evaluación de incertidumbre producida por Gemini.

Los contextos C preparados contienen recuperación verificada no vacía de 1A. Los
tests comprueban que B/C usan modelo, política y configuración idénticos, que B solo
recibe original y que C añade exclusivamente recuperación. Los mensajes enviados
no incluyen expectativas, criterios del revisor ni etiquetas de 1B.

**Ninguna solicitud C real llegó a enviarse.** No se ha comprobado que el proveedor
recibiera esas recuperaciones ni que produjera citas correctas. Tampoco se observaron
atribuciones erróneas de Base64 original a una fuente recuperada o alucinaciones:
son aspectos sin datos, no defectos resueltos. Literalidad, validación estructural
y soporte semántico siguen siendo verificaciones separadas; los mocks no sustituyen
salidas reales ni adjudicación humana.

Evidencias: [resumen](../artifacts/gemini_36/summary.json),
[revisión de ausencia de datos](../artifacts/gemini_36/quality_review.json).

## Presupuesto, cuota y seguridad

| Concepto | Resultado |
|---|---|
| Metadatos históricos | 2, sin nuevas consultas |
| Generación histórica 3.8 | 1, HTTP 503, preservada |
| Generaciones nuevas 3.6 | 1, HTTP 400 |
| Reservas globales consumidas | **4/12** |
| Reservas globales sin utilizar | **8** |
| Salidas de modelo utilizables en 3.6 | 0 |
| Tokens reales consumidos | Desconocidos; el error no informó contadores |
| Saldo real de cuota del proveedor | No consultado; distinto del ledger local |

No se devuelve la reserva fallida. No se infiere un saldo RPD de 19 ni consumo de
tokens cero. Free tier y sus límites proceden de la confirmación del propietario;
el agente no habilitó facturación ni usó herramientas de pago. La prueba no descargó
modelos, no ejecutó Ollama, PowerShell, Base64 recuperado o código generado, y no
accedió a URLs de las muestras. La clave se leyó solo desde el backend y nunca se
incluyó en frontend, VITE, prompts, resultados o informes.

## Pruebas e integridad

**973 pruebas backend aprobadas, 28 frontend aprobadas y build TypeScript/Vite correcto.**
`pip check` pasó. Persiste la advertencia conocida Starlette/httpx, sin fallo.
Las ocho pruebas nuevas verifican selección explícita de 3.6, omisión de parámetros,
pensamiento medium, presupuestos compartidos de tres a siete, conservación del prefijo
histórico, paradas sin reintentos, equivalencia B/C, citas recuperadas simuladas,
estado FastAPI local y ausencia de filtraciones. Los tests de red usan exclusivamente
SDK y transporte simulado; no prueban calidad del modelo real.

Se añadió `gemini36.py`, `experiments/gemini_36.py` y
`backend/tests/pipelines/test_gemini36.py`. La modificación del adaptador común solo
separa la construcción de configuración, conservando la de 3.8/2.5. FastAPI y React
conservan el contrato de aplicación y el proveedor predeterminado. No se reescribió
ningún resultado de Qwen, 3.8, piloto v2 o plan r2.

[Validación](../artifacts/gemini_36/validation.json),
[integridad](../artifacts/gemini_36/integrity_after.json),
[auditoría de secretos](../artifacts/gemini_36/security_audit.json).
Los tres primeros registros del ledger se conservaron byte por byte; solo se añadió
la cuarta reserva. Trabajo local en `develop`, sin staging ni operaciones Git de escritura.

## Recomendación

**No ampliar todavía las pruebas de desarrollo ni seleccionar formalmente 3.6 con
esta evidencia.** Primero conviene diagnosticar de forma segura el HTTP 400 y la
compatibilidad remota de la petición. La causa concreta sigue sin determinar; no se
debe cambiar a ciegas un parámetro y gastar otra reserva. Una nueva ejecución requerirá
decisión expresa y un plan prospectivo, conservando este resultado negativo.

El adaptador queda preparado, las ocho reservas restantes se conservan y 3.5 Flash-Lite
queda únicamente como alternativa para una decisión posterior: no se configuró ni
se llamó. No hay datos para afirmar superioridad de disponibilidad o semántica frente
a 3.8 o Qwen. Los cuatro casos previstos serían solo diagnósticos incluso si terminaran
bien; se mantienen pendientes selección independiente, adjudicación semántica humana,
cobertura suficiente y congelación del protocolo. No se aprobó científicamente Gemini,
no se migró el proveedor principal y no se inició Fase 4.
