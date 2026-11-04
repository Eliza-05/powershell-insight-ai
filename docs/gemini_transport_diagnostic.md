# Diagnóstico de transporte de Gemini — 2 de noviembre de 2026

Continuación posterior: [diagnóstico de generación r2](gemini_viability.md).
Con autorización expresa y cuota declarada por el propietario, se intentó G03-B:
HTTP 503 y parada sin reintento. Estado actual **3/12 reservas, un intento de generación
fallido y nueve reservas sin utilizar**. Las cifras 2/12 de la sección siguiente
corresponden al cierre anterior de la segunda consulta de metadatos.

## Actualización: segunda consulta real autorizada

**El segundo listado funcionó y contiene `models/gemini-3.8-flash`.** La autorización
expresa del propietario se registró el **2026-11-03 a las 02:28:25.499021 UTC**
(2 de noviembre, 21:28:25, America/Bogota). La segunda reserva se inició a las
**02:28:36.724774 UTC**, con el SDK oficial y el transporte corregido.

Se recibió una única página con **60 modelos**, sin token de página adicional.
`gemini-3.8-flash` anuncia `generateContent` y soporte de thinking. El campo `version`
del listado devolvió literalmente `3.0`; se conserva sin reinterpretarlo como una
versión de inferencia probada. No se ejecutó generación ni se cambió el candidato.

**Estado actual: 2/12 reservas usadas, ambas de metadatos; 0 inferencias.** Quedan
como máximo **10 reservas para futuras generaciones**. No hubo reintentos, consultas
adicionales, activación de facturación ni inicio de Fase 4. La autenticación quedó
aceptada para `models.list` en esta consulta; **la cuota gratuita positiva para
generación sigue sin verificar**. El controlador de éxito no persistió el estado
HTTP numérico y no se añade uno supuesto al registro.

Antes de enviar se verificaron los hashes de los nueve archivos documentados,
las versiones de dependencias, el plan r2, el fingerprint de la petición y el hash
del ledger de una sola entrada. El ledger previo tenía SHA-256
`b8d8fcf47f5727a000c2699c262a28262563c811fb47c8e5d495accbbbd302cf`.
Después se comprobaron los bytes de la primera entrada, las dos únicas reservas y
la integridad de 168 archivos protegidos: solo cambió el ledger mediante el append
autorizado. No se modificó código del adaptador/controlador ni el índice o HEAD de Git.

Evidencias de esta ejecución:

- [Autorización UTC](../artifacts/gemini_transport_diagnostic/metadata_authorization_02.json).
- [Comprobaciones previas](../artifacts/gemini_transport_diagnostic/metadata_02_precheck.json).
- [Listado conservado](../artifacts/gemini_transport_diagnostic/metadata_retry_02.json).
- [Comprobaciones posteriores](../artifacts/gemini_transport_diagnostic/metadata_02_postcheck.json).
- [Informe anterior conservado](../artifacts/gemini_transport_diagnostic/report_before_metadata_02.md).

### Qué verificar personalmente antes de autorizar inferencias

En [AI Studio](https://aistudio.google.com/rate-limit), seleccionar el **proyecto
asociado a la clave que ya está en `.env`**, sin copiar ni compartir esa clave:

1. Confirmar **Free tier** para ese proyecto y que no tenga facturación de pago
   habilitada. No pulsar opciones para activar o vincular facturación.
2. Confirmar que la cuota gratuita de **`gemini-3.8-flash` para `generateContent`**
   sea positiva y aplicable a ese proyecto y región. El listado de modelos no prueba
   ese permiso ni la cuota efectiva de generación.
3. Anotar los límites **RPM, TPM y RPD**, cualquier otro límite que se muestre,
   el uso actual, el saldo restante y la hora/zona del reinicio. Para ejecutar el
   lote completo deben quedar al menos **10 solicitudes de generación**, además de
   capacidad de tokens y cadencia suficientes; el presupuesto local no es saldo del proveedor.
4. Si hay una restricción de clave/API/proyecto o aviso de cuota cero, comprobarla
   personalmente y describir solo el estado, sin claves, cabeceras ni cuerpos sensibles.

Después, comunicar esos valores no sensibles y autorizar expresamente la reanudación
del plan r2 de hasta diez inferencias sintéticas. **La autorización de esta segunda
consulta ya está consumida y no habilita inferencias ni un tercer listado.**

## Diagnóstico técnico y antecedentes

**Se confirmó y corrigió un defecto local de doble descompresión de respuestas.**
Una respuesta gzip simulada reproducía exactamente `gemini_transport_error` con
el SDK instalado. Tras la corrección, el mismo test pasa. DNS, TCP 443 y TLS con
validación de certificado y nombre del host funcionan en las comprobaciones actuales.

Durante el diagnóstico previo no se hizo ninguna solicitud HTTP a Gemini y se cerró
con **1/12 reservas y 0 inferencias**. La segunda consulta autorizada descrita arriba
llevó el contador a **2/12**, conservando intactos los bytes del primer intento.
No se borró, reinició ni reescribió el contador.

El primer intento guardó una categoría genérica y no conservó excepción, estado
HTTP o codificación de respuesta. Por ello **no se puede demostrar retrospectivamente
que aquel intento fallara por gzip**. La reproducción confirma un defecto capaz de
producir ese mismo error, no una reconstrucción del tráfico histórico. Tampoco hay
prueba de autenticación válida, modelos accesibles o cuota efectiva del proyecto en
ese primer registro. La segunda consulta sí acredita acceso autenticado al listado
y presencia del modelo, pero no cuota gratuita positiva de generación.

## Comprobaciones realmente realizadas

Evidencia: [network_checks.json](../artifacts/gemini_transport_diagnostic/network_checks.json).
Las conexiones se ejecutaron desde Python con permiso de red, sin cliente HTTP ni
SDK en esa comprobación. Solo resolución DNS, apertura TCP y handshakes TLS, sin
enviar datos de aplicación ni credenciales. Las pruebas simuladas usan claves ficticias.

| Comprobación | Resultado observado | Límite de la conclusión |
|---|---|---|
| DNS del host público de Gemini | Correcto; 8 direcciones devueltas | No demuestra disponibilidad histórica ni prueba individual de todas las direcciones |
| TCP a `generativelanguage.googleapis.com:443` | Conexión correcta | No se enviaron HTTP GET/HEAD/POST |
| TLS con `certifi`, equivalente al almacén predeterminado de HTTPX | TLS 1.3; certificado y nombre del host verificados | No se desactivó validación ni se instalaron certificados |
| TLS con contexto estándar del sistema | TLS 1.3; validación correcta | Es otra comprobación de handshake, no autenticación de API |
| Variables de proxy y CA del proceso | HTTP_PROXY, HTTPS_PROXY, ALL_PROXY, NO_PROXY, SSL_CERT_FILE y SSL_CERT_DIR ausentes | No se imprimieron valores, hosts privados, rutas ni credenciales de proxy |
| Descubrimiento Python de proxy | Ningún esquema de proxy encontrado | Estado del proceso observado, no de todas las aplicaciones del equipo |
| WinINET del usuario | ProxyEnable, ProxyServer y AutoConfigURL no configurados | Consulta de registro en modo de lectura |
| WinHTTP | Informa acceso directo | No se modificó la configuración |
| Firewall de Windows | Perfiles Domain, Private y Public activos; se conservaron valores brutos de DefaultOutboundAction | No se enumeraron todas las reglas ni filtros por aplicación; no se afirma ausencia de restricciones HTTP |
| Credencial | Ausente del entorno exportado del proceso, pero disponible correctamente para Python desde `.env` raíz | Diseño deliberado: se pasa explícitamente al SDK sin exportar dotenv ni mostrar el valor |
| Dependencias | `pip check`: sin dependencias incompatibles declaradas; SDK real funciona con HTTP simulado | No demuestra compatibilidad del servicio remoto sin una consulta autorizada |

La primera lectura del firewall desde el entorno restringido no estuvo disponible.
Una lectura posterior con acceso suficiente devolvió los perfiles; no se confundió
ese impedimento del entorno de ejecución con un bloqueo de red de Windows. Evidencias:
[windows_checks.json](../artifacts/gemini_transport_diagnostic/windows_checks.json) y
[firewall_read_check.json](../artifacts/gemini_transport_diagnostic/firewall_read_check.json).
No se modificó ninguna regla ni protección.

Versiones observadas: `google-genai 2.34.0`, `python-dotenv 1.2.4`, `httpx 0.28.1`,
`httpcore 1.0.9`, `certifi 2026.10.23`, `pydantic 2.14.2`, `tenacity 9.1.4` y
`google-auth 2.62.0`. No se actualizaron dependencias ni se descargaron modelos.

HTTPX documenta que `trust_env=False` ignora proxies y CA del entorno y que la
verificación utiliza `certifi` de forma predeterminada. Se conservaron esos controles;
las comprobaciones actuales no justifican habilitar proxies ni cambiar certificados.
[Variables de HTTPX](https://www.python-httpx.org/environment_variables/),
[verificación TLS](https://www.python-httpx.org/advanced/ssl/).

Un handshake correcto no excluye una incidencia intermitente anterior, un filtro de
HTTP, restricciones de clave/proyecto, región no admitida o un rechazo del proveedor.
El diagnóstico de red no verificó esas condiciones mediante HTTP. La consulta posterior
se limitó al listado autorizado; no probó generación ni cuota efectiva.

## Defecto local y corrección

El transporte utilizaba `response.iter_bytes()`, que ya entrega el cuerpo descomprimido.
Luego construía otra `httpx.Response` con esos bytes y todas las cabeceras originales,
incluida `Content-Encoding: gzip`. HTTPX intentaba descomprimir de nuevo y lanzaba
`DecodingError`; `_error` lo convertía en el inespecífico `gemini_transport_error`.
Los tests anteriores utilizaban JSON sin compresión y no cubrían esa condición.

Ahora se conserva el cuerpo decodificado y se reconstruye la respuesta con Content-Type
y longitud calculada por HTTPX. Se eliminan cabeceras de compresión, transferencia,
cookies y autenticación del intermediario. Los límites de tamaño y las comprobaciones
de eco de credenciales siguen aplicándose al cuerpo decodificado. La respuesta original
se cierra incluso en fallos. El estado HTTP se registra inmediatamente después de
recibirlo, antes de leer/descomprimir el cuerpo.

La reproducción incluye tanto respuestas gzip precargadas como streams comprimidos
similares al transporte real, éxitos y errores HTTP. Véanse
[reproduction.json](../artifacts/gemini_transport_diagnostic/reproduction.json) y
[tests](../backend/tests/pipelines/test_gemini_transport.py).

## Categorías seguras y privacidad

`gemini_errors.py` recorre causas y contextos de excepción con límite y detección de
ciclos, sin convertir excepciones a texto. Reconoce DNS, certificados TLS, handshake,
timeout, conexión rechazada, acceso denegado, red inalcanzable, proxy, protocolo HTTP,
decodificación de respuesta y fallos locales del cliente. HTTP 400/401/403/404/408/429,
redirecciones y errores 5xx se distinguen de los fallos de conexión.

El diagnóstico persistible contiene solo `category` y `http_status`, si se conoce.
No incluye mensajes originales, argumentos, tracebacks, cabeceras, direcciones con
parámetros, claves ni cuerpos de errores HTTP. Una causa SSL anidada en ConnectError
se clasifica como TLS; no se deduce TLS analizando texto potencialmente sensible.

Se silenciaron también los logs del espacio de nombres real `google_genai`, además de
`google.genai`, HTTPX y httpcore. La clave sigue pasando explícitamente desde el cargador
del backend; la prueba del SDK confirma el uso de ese cliente HTTP personalizado.
No se imprime ni copia la clave a los nuevos documentos o evidencias.

## Reintentos y contabilidad

Se verificó en el código instalado y en tests que el SDK usa
`HttpRetryOptions(attempts=1)`, el transporte HTTP usa `retries=0`, no sigue
redirecciones y tiene `trust_env=False`. Los tests de DNS, TLS, timeout, conexión
rechazada, HTTP 429/503 y compresión verifican **un solo intento físico y una reserva**.
No se usan APIs Interactions ni funciones automáticas del SDK.

La reserva se escribe y sincroniza antes de llamar al transporte interno. Los fallos
después de reservar siguen consumiendo presupuesto. Los bloqueos locales previos al
envío no gastan reservas. Se conserva el bloqueo exclusivo, el rechazo de duplicados
y el máximo global de 12 entre metadatos e inferencias. Un error de lectura posterior
a HTTP 200 también cuenta: no se devuelve presupuesto por una respuesta no interpretable.

El segundo listado estuvo bloqueado por defecto y se ejecutó una sola vez tras la
autorización expresa. Se añadió una excepción acotada para
una autorización explícita del propietario: operación exacta `models.list`, hash de
los bytes del ledger previo, vigencia de una hora, máximo de dos metadatos y doce
solicitudes totales. Solo funciona cuando existe exactamente el primer intento de
metadatos y el fingerprint de la consulta coincide. Se comprueba dentro del lock.
Una vez reservada la segunda consulta, el mismo permiso no permite una tercera,
aunque la segunda falle. La primera línea del diario no se altera.

La autorización local es un registro de la decisión del responsable, no una firma
criptográfica ni una prueba de cuota. La plantilla conserva `authorized=false`;
el registro específico `metadata_authorization_02.json` autorizó únicamente la segunda
consulta y ya fue consumido. No puede reutilizarse para una tercera.

## Procedimiento preparado para la segunda consulta

El comando siguiente es **solo vista previa**, sin red y sin consumir reservas:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.gemini_metadata_retry
```

La vista previa mostró una reserva usada, segunda reserva propuesta y diez generaciones
máximas posteriores. El procedimiento siguiente se completó para esta autorización;
**no debe repetirse**:

1. El responsable autoriza expresamente en el chat **una única segunda consulta de
   modelos**, sin inferencias ni cambio de modelo. Esta autorización posterior fue
   recibida expresamente en el chat.
2. Después de recibirla, registrar una copia de
   `artifacts/gemini_transport_diagnostic/metadata_authorization.template.json`,
   con `authorized=true`, `source=explicit_owner_authorization` y `confirmed_at` UTC
   real. Conservar el hash del ledger, operación y máximos. No incluir ninguna clave.
3. Comprobar que el ledger sigue intacto y el plan prospectivo coincide. El controlador
   rechaza antes de crear el cliente una aprobación ausente, falsa, expirada, vinculada
   a otro estado del diario o que amplíe límites.
4. Solo tras esa aprobación, se ejecutó una vez:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.gemini_metadata_retry --execute --authorization artifacts/gemini_transport_diagnostic/metadata_authorization_02.json
```

Ese comando reserva y envía **una sola página** del listado. No pagina, no reintenta,
no invoca generación y no cambia el candidato `gemini-3.8-flash`. Conserva el resultado
en `artifacts/gemini_transport_diagnostic/metadata_retry_02.json`, sin sobrescribir
los registros anteriores. Si el modelo no aparece, se informa; no se elige otro.
Si falla, se conserva la categoría segura y se detiene. En la ejecución autorizada
se recibió el listado correctamente; no se volvió a ejecutar el comando.

El listado recibido prueba acceso autenticado al endpoint de metadatos en ese momento;
**no demostraría cuota gratuita positiva para generación**. El comando no habilita
automáticamente B/C ni modifica la aplicación predeterminada.

## Ajuste prospectivo del presupuesto

[plan_r2.json](../artifacts/gemini_transport_diagnostic/plan_r2.json) es una revisión
prospectiva, aún no autorizada para ejecutar generación: **2 metadatos + 10 inferencias
= 12 reservas máximas**. Se conservan los planes r0/r1 y todos sus resultados locales.
No se modificaron las muestras ni sus etiquetas y no hubo nuevas salidas de modelo.

Orden preparado: G03-B, G03-C, G06-B, G06-C, G01-B, G09-B, G04-B, G07-B, G08-B, G05-B.
Las dos C con recuperación verificada no vacía y sus controles B aparecen primero.
Después se priorizan benignidad/consulta legítima, inyección e incertidumbre, bloque
inactivo, modificación de defensas, almacén de credenciales y descarga remota.

Se difiere G02-B, el control IEX aislado con entrada conocida. G09 conserva el criterio
de invocación externa B02 con entrada desconocida y G04 el negativo de bloque no invocado,
pero esa sustitución reduce aislamiento diagnóstico y no equivale a haber probado G02.
El plan mantiene exactamente `gemini-3.8-flash`, instrucciones y parámetros de B/C.
El antiguo `run` de once inferencias no es el procedimiento para este futuro lote.

## Datos que debe comprobar el responsable en AI Studio

- Que el proyecto asociado a la clave de `.env` sea el que muestra **Free tier**, y
  que no tenga facturación de pago habilitada. No activarla para superar un bloqueo.
- Que `gemini-3.8-flash` tenga disponibilidad y cuota gratuita positiva para ese
  proyecto y región; su aparición en documentación o un listado no basta.
- RPM, TPM, RPD, uso actual, cuota restante y hora de reinicio mostrados en
  [los límites del proyecto](https://aistudio.google.com/rate-limit).
- Estado de la API y restricciones de la clave/proyecto si la consulta autorizada
  devuelve 401/403; revisarlas personalmente sin pegar la clave ni desactivar controles
  de forma indiscriminada.

La confirmación anterior del nivel gratuito sigue siendo una declaración del usuario;
los valores exactos y la cuota efectiva permanecen sin verificar. El acceso autenticado
al listado sí se comprobó en la segunda consulta, con el alcance descrito arriba.
No se aceptan mensajes de error con credenciales como material para el chat.

## Validación e integridad

Las regresiones y la auditoría de esta entrega se documentan en
[validation.json](../artifacts/gemini_transport_diagnostic/validation.json),
[backend_tests.xml](../artifacts/gemini_transport_diagnostic/backend_tests.xml) e
[integrity_after.json](../artifacts/gemini_transport_diagnostic/integrity_after.json).
Se incluyen pruebas de autorización caducada/ausente, hash incorrecto, tercera consulta
bloqueada y límite de diez generaciones después de dos metadatos, usando diarios temporales
y respuestas ficticias. Ningún test consulta la API real ni utiliza la clave real para HTTP.

En el diagnóstico no hubo llamadas nuevas de Gemini. La autorización posterior produjo
exactamente una segunda consulta de metadatos, sin inferencias, descargas de modelos,
ejecución de muestras, cambios de facturación o certificados, nuevas ejecuciones de Ollama
ni inicio de Fase 4.
Se preservaron los resultados históricos, el índice Git y la rama `develop`; no se realizaron
operaciones Git de escritura. La siguiente acción es comprobar en AI Studio la cuota
gratuita efectiva de `gemini-3.8-flash` y sus límites antes de autorizar inferencias.
