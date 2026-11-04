# Diagnóstico específico del HTTP 400 de Gemini 3.6

**Clasificación final: causa indeterminada.** Se reconstruyó el cuerpo HTTP exacto,
pero no se identificó una infracción demostrable que explique el 400 histórico.
El cuerpo de aquel error fue descartado y no se puede recuperar. No se inventó su
mensaje ni se atribuyó el rechazo a un parámetro sin evidencia.

**Cero solicitudes nuevas a la API de Gemini; ledger intacto en 4/12.** Todos los envíos del
SDK durante este encargo usaron `httpx.MockTransport`, una credencial ficticia y
respuestas simuladas. No hubo inferencia remota, DNS/TCP de diagnóstico, consultas
de modelos, cambios de dependencias o proveedor, facturación ni Fase 4.

## Petición HTTP reconstruida, no solo objetos Python

Se tomó `operational.request` del [G03-B real](../artifacts/gemini_36/G03_B.json),
se reintrodujo en **google-genai 2.34.0** y se capturaron los bytes al llegar a la
capa HTTP simulada. No se cargó `.env` para reconstruirlos ni se conservaron cabeceras.
La prueba usa una clave sintética explícita; no la clave real.

Método: **POST**. Ruta: **`/v1beta/models/gemini-3.6-flash:generateContent`**.
El fingerprint calculado con el mismo método del ledger coincide exactamente:

`b1caa8f279866234dc030a322c28594ddfb123fdbb58d9259421f19bfef1d762`

Este fingerprint cubre método, ruta y texto exacto del body, incluida su serialización.
No afirma reconstrucción bit a bit de cabeceras, TLS o transporte comprimido.
El SHA-256 independiente del body reconstruido es:

`b1fd2c21d7adc7f0821ec993b60eec99df9c7a8a64c508fd03dea54369d5aa81`

Se conservó el [JSON HTTP completo](../artifacts/gemini_36_http400/complete_historical.wire.json)
y la [evidencia de reconstrucción](../artifacts/gemini_36_http400/differential_results.json).
Ningún byte del artefacto histórico o su plan se modificó.

| Elemento real | Comprobación |
|---|---|
| Versión de API | `v1beta`, coherente con la ruta documentada de generateContent |
| `contents` | Un turno `user`, con texto JSON que contiene solo el original sintético |
| `systemInstruction` | Política de análisis histórica, separada del contenido de usuario |
| `maxOutputTokens` | 8192 |
| `responseMimeType` | `application/json` |
| Campo de esquema | **`responseJsonSchema`**, no `responseSchema`; no se envían ambos |
| `thinkingConfig` | Contiene `include_thoughts: false` y `thinking_level: MEDIUM` |
| Muestreo y candidatos | Ausentes temperature, topP, topK, seed, candidateCount y penalizaciones |
| Prefill de modelo | Ausente; el último turno es `user` |
| Herramientas | Vacías; funciones automáticas deshabilitadas en el cliente |

La [referencia de generateContent](https://ai.google.dev/api/generate-content)
documenta v1beta, JSON mode y configuración de pensamiento. La configuración no mezcla
thinkingLevel y thinkingBudget ni utiliza un nivel desconocido. La [guía 3.6](https://aistudio.google.com/docs/whats-new-gemini-3.6)
motiva la omisión de los controles de muestreo y candidatos; eso ya se había aplicado
antes del intento fallido, no es una corrección posterior de aquel intento.

## Nombres de campos y soporte real del SDK instalado

En `google/genai/models.py`, `_GenerateContentConfig_to_mldev` convierte los nombres
externos a camelCase, pero copia el objeto `thinking_config` sin convertir sus campos
internos. De ahí el snake_case observado en los bytes. `types.ThinkingConfig` admite
esos campos y el enum MEDIUM en esta versión instalada.

**Ese detalle no demuestra un error.** [ProtoJSON](https://protobuf.dev/programming-guides/json/)
admite los nombres camelCase y los originales del protobuf. Las pruebas estáticas
aceptan las dos representaciones y detectan campos desconocidos o alias duplicados.
No hay evidencia de que el endpoint rechazara estos alias, ni confirmación remota
que permita declararlos la causa del 400.

El SDK también distingue dos caminos de esquema: `response_json_schema` transmite
JSON Schema mediante `responseJsonSchema`; `response_schema` realiza conversión a
Schema/OpenAPI, expandiendo referencias y cambiando la representación. Un control
local adicional verificó esa conversión. Cambiar de campo produce otra petición y
no constituye una solución demostrada para este caso.

No se actualizó el SDK: todos los campos utilizados existen y se serializan en la
versión instalada. Una actualización no está justificada por la evidencia disponible.

## Inspección concreta del JSON Schema

El esquema capturado tiene **2317 bytes en JSON canónico compacto**, **8 definiciones**, **8 propiedades raíz
obligatorias** y **9 referencias internas resueltas**. No contiene ciclos, referencias
externas, alternativas anyOf/oneOf, allOf, condicionales ni rangos numéricos. Las referencias
no tienen hermanos incompatibles con el subconjunto documentado. Los campos requeridos
existen y los límites de arrays tienen tipos y rangos consistentes.

La inspección encontró dos puntos concretos, con alcances distintos:

1. Hay **12 restricciones minLength/maxLength**. Son JSON Schema válido, pero Google
   documenta que las ignora durante la decodificación. Por tanto, no garantizan longitud
   en el proveedor y deben seguir validándose con Pydantic. No demuestran una causa de 400.
2. Hay **dos niveles de arrays anidados**, profundidad máxima de datos expandida de **6**,
   hasta **7 comportamientos ×16 evidencias =112 citas** y otros arrays con máximos 16/32.
   Son capacidades permitidas por el esquema. Podrían influir en la complejidad de la
   gramática del proveedor, pero no hay un umbral publicado ni un error histórico que
   permita afirmar que lo superan.

`$defs`, `$ref`, additionalProperties, enums y límites de arrays están documentados en
el subconjunto JSON Schema. La guía advierte sobre complejidad, pero no permite inferir
rechazo solo por el tamaño del documento. [Salida estructurada](https://ai.google.dev/gemini-api/docs/structured-output).

La validez estructural del esquema no garantiza que el compilador remoto lo acepte,
ni que una salida del modelo respete sus invariantes semánticas. Los validadores de
coherencia de la aplicación también exigen condiciones que no expresa este JSON Schema.
No se debilitó ninguno de ellos ni se redujeron límites del esquema histórico.

El [inventario detallado](../artifacts/gemini_36_http400/schema_inventory.json) enumera
las rutas y valores de todas las restricciones, referencias y arrays. Es un comprobador
estático acotado al subconjunto documentado; no se presenta como metavalidador completo
de JSON Schema ni como emulación del compilador de Google. No se instaló jsonschema
ni otra dependencia para fingir esa equivalencia.

## Pruebas diferenciales sin Google

Cada variante atraviesa el serializador del SDK y termina en un mock, nunca en un
transporte real. El mock devuelve un stub; su HTTP 200 **no prueba aceptación remota,
validez de una respuesta respecto del esquema ni calidad del modelo**. La inspección
del JSON final es una comprobación separada.

| Variante | Campos relevantes en generationConfig | Resultado local |
|---|---|---|
| Texto básico | maxOutputTokens | Serialización y formato acotado correctos |
| JSON simple | responseMimeType + responseJsonSchema sencillo | Correctos |
| Esquema completo | responseMimeType + responseJsonSchema histórico | Correctos; sin palabras clave desconocidas según el perfil |
| Pensamiento | thinkingConfig MEDIUM | Correctos; alias protobuf admitidos por el comprobador |
| Petición completa de la aplicación | Esquema, pensamiento y política originales | Correctos; fingerprint exacto del intento histórico |

Los controles negativos detectan dos esquemas mutuamente excluyentes, MIME faltante,
pensamiento por nivel y presupuesto simultáneos, campo de pensamiento desconocido,
alias duplicado, referencia inexistente, límite de array mal tipado y required inválido.
Las pruebas bloquean DNS, conexiones y `HTTPTransport.handle_request` para asegurar
que los controles diferenciales no puedan contactar a Google.

## Defecto de diagnóstico identificado y corregido

El transporte descartaba todos los detalles estructurados de los errores y conservaba
solo categoría y código HTTP. **Esa pérdida de información sí es demostrable y está
corregida**, pero no es la causa demostrada del rechazo histórico.

El nuevo extractor conserva únicamente:

- Código HTTP y `error.code` numérico válido.
- `error.status` si pertenece a una lista cerrada de códigos RPC.
- Rutas conocidas de `google.rpc.BadRequest.fieldViolations[].field`, con gramática,
  longitud, segmentos y posiciones limitados.
- Motivos de `google.rpc.ErrorInfo.reason` solo si están en una lista cerrada.

Se descartan message, description, metadata, domain, DebugInfo, cabeceras, valores de
argumentos, nombres arbitrarios y cuerpos completos. No se analiza un mensaje de texto
para inventar una ruta. Si el proveedor no devuelve detalles estructurados reconocibles,
se conserva solo lo seguro disponible. Los ejemplos INVALID_ARGUMENT o API_KEY_INVALID
de los tests son **simulados**, no campos recuperados del error histórico.

El filtro aplica antes de descartar el cuerpo, se reinicia en cada operación y no
habilita reintentos. Las pruebas comprueban que mensajes, claves ficticias, URL,
metadatos y rutas maliciosas no llegan al diagnóstico. El formato elegido corresponde
a los [detalles estructurados de errores de Google](https://google.aip.dev/193).

## Única prueba real mínima propuesta — no ejecutada

No hay una solución causal confirmada que pueda darse por validada. Se propone
**una sola generación G03-B de control**, manteniendo modelo 3.6, política, contenido,
JSON mode, pensamiento y presupuesto originales, **omitiendo únicamente
`generationConfig.responseJsonSchema`**. Permite aislar el componente de esquema completo
sin cambiar de proveedor o añadir otro caso.

- Si devuelve HTTP 200, demostraría que el resto de esa petición y JSON mode pueden
  aceptarse sin el esquema completo, en ese intento. No probaría retrospectivamente
  que el esquema causó el 400 ni certificaría soporte semántico.
- Si devuelve HTTP 400, mostraría que el rechazo persiste sin el esquema; los nuevos
  campos estructurados seguros podrían localizar el argumento, si el proveedor los envía.
- Costo máximo: **una reserva**, de **4/12 a 5/12**, quedando siete. Sin metadatos,
  reintentos o inferencias adicionales. Requiere autorización posterior y confirmación
  vigente de cuota gratuita.

Se prepararon [plan prospectivo v2](../artifacts/gemini_36_http400/prospective_probe_v2.json)
y [JSON HTTP propuesto](../artifacts/gemini_36_http400/prospective_probe.wire.json),
con hashes del ledger y de los cuerpos histórico/nuevo. Una prueba local verifica que
la omisión del esquema es la **única diferencia** del JSON. El plan tiene
`authorized=false`; no se añadió un ejecutor de red. El esquema, petición y resultados
de la prueba histórica permanecen intactos.

## Validación y cierre

**990 pruebas backend aprobadas**, incluidas 17 nuevas específicas de este diagnóstico.
`pip check` pasó; sin cambios de dependencias. Se conserva la advertencia conocida de
Starlette/httpx. No se repitieron pruebas frontend porque no se modificó su código.

Evidencia: [JUnit](../artifacts/gemini_36_http400/backend_tests.xml),
[validación](../artifacts/gemini_36_http400/validation.json),
[integridad](../artifacts/gemini_36_http400/integrity_after.json).
Se conservaron todas las pruebas y artefactos anteriores, así como los bytes del ledger,
el índice Git y HEAD. Nuevos fuentes: `gemini_error_details.py`,
`experiments/gemini_400_offline.py` y `test_gemini400.py`; el transporte común solo añade
el filtro seguro y su reinicio. No se cambiaron gemini36.py, política, esquema o parámetros
del experimento ejecutado. Rama `develop`, cambios locales sin staging ni Git de escritura.
