# Diagnóstico de transporte de Gemini — 2 de noviembre de 2026

**Se confirmó y corrigió un defecto local de doble descompresión de respuestas.**
Una respuesta gzip simulada reproducía exactamente `gemini_transport_error` con
el SDK instalado. Tras la corrección, el mismo test pasa. DNS, TCP 443 y TLS con
validación de certificado y nombre del host funcionan en las comprobaciones actuales.

**No se hizo ninguna nueva solicitud HTTP a Gemini.** El ledger original conserva
su único intento y sus bytes; siguen **1/12 reservas consumidas y 0 inferencias**.
No se borró, reinició ni reescribió el contador.

El primer intento guardó una categoría genérica y no conservó excepción, estado
HTTP o codificación de respuesta. Por ello **no se puede demostrar retrospectivamente
que aquel intento fallara por gzip**. La reproducción confirma un defecto capaz de
producir ese mismo error, no una reconstrucción del tráfico histórico. Tampoco hay
prueba de autenticación válida, modelos accesibles o cuota efectiva del proyecto.

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
Nada de eso se verificó enviando otra solicitud, porque esa acción sigue pendiente
de autorización.

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

El segundo listado sigue bloqueado por defecto. Se añadió una excepción acotada para
una autorización explícita del propietario: operación exacta `models.list`, hash de
los bytes del ledger previo, vigencia de una hora, máximo de dos metadatos y doce
solicitudes totales. Solo funciona cuando existe exactamente el primer intento de
metadatos y el fingerprint de la consulta coincide. Se comprueba dentro del lock.
Una vez reservada la segunda consulta, el mismo permiso no permite una tercera,
aunque la segunda falle. La primera línea del diario no se altera.

La autorización local es un registro de la decisión del responsable, no una firma
criptográfica ni una prueba de cuota. La plantilla entregada tiene `authorized=false`;
no se creó ninguna autorización habilitante ni se ejecutó el segundo listado.

## Procedimiento preparado para la segunda consulta

El comando siguiente es **solo vista previa**, sin red y sin consumir reservas:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.gemini_metadata_retry
```

Se ejecutó y mostró una reserva usada, segunda reserva propuesta y diez generaciones
máximas posteriores. Los pasos siguientes están pendientes:

1. El responsable autoriza expresamente en el chat **una única segunda consulta de
   modelos**, sin inferencias ni cambio de modelo. La petición actual de diagnóstico
   no concede esa autorización.
2. Después de recibirla, registrar una copia de
   `artifacts/gemini_transport_diagnostic/metadata_authorization.template.json`,
   con `authorized=true`, `source=explicit_owner_authorization` y `confirmed_at` UTC
   real. Conservar el hash del ledger, operación y máximos. No incluir ninguna clave.
3. Comprobar que el ledger sigue intacto y el plan prospectivo coincide. El controlador
   rechaza antes de crear el cliente una aprobación ausente, falsa, expirada, vinculada
   a otro estado del diario o que amplíe límites.
4. Solo tras esa aprobación, ejecutar:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.gemini_metadata_retry --execute --authorization RUTA_AL_REGISTRO_DE_APROBACION.json
```

Ese comando reserva y envía **una sola página** del listado. No pagina, no reintenta,
no invoca generación y no cambia el candidato `gemini-3.8-flash`. Conserva el resultado
en `artifacts/gemini_transport_diagnostic/metadata_retry_02.json`, sin sobrescribir
los registros anteriores. Si el modelo no aparece, se informa; no se elige otro.
Si falla, se conserva la categoría segura y se detiene. Ninguno de los pasos de
ejecución se realizó en esta entrega.

Un listado recibido probaría acceso autenticado al endpoint de metadatos en ese momento;
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
los valores exactos, el acceso autenticado y la cuota efectiva permanecen sin verificar.
No se aceptan mensajes de error con credenciales como material para el chat.

## Validación e integridad

Las regresiones y la auditoría de esta entrega se documentan en
[validation.json](../artifacts/gemini_transport_diagnostic/validation.json),
[backend_tests.xml](../artifacts/gemini_transport_diagnostic/backend_tests.xml) e
[integrity_after.json](../artifacts/gemini_transport_diagnostic/integrity_after.json).
Se incluyen pruebas de autorización caducada/ausente, hash incorrecto, tercera consulta
bloqueada y límite de diez generaciones después de dos metadatos, usando diarios temporales
y respuestas ficticias. Ningún test consulta la API real ni utiliza la clave real para HTTP.

No hubo llamadas nuevas de Gemini, inferencias, descargas de modelos, ejecución de muestras,
cambios de facturación o de certificados, nuevas ejecuciones de Ollama ni inicio de Fase 4.
Se preservaron los resultados históricos, el índice Git y la rama `develop`; no se realizaron
operaciones Git de escritura. La siguiente acción es la autorización expresa de la única
consulta de metadatos descrita arriba.
