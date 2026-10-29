# Taxonomía de comportamientos

> **Versión provisional (v0.1).** Debe revisarse y congelarse antes de etiquetar el dataset experimental. Los ejemplos son conceptuales y no constituyen código ejecutable.

## 1. Conceptos que se distinguen

| Concepto | Pregunta que responde | Ejemplo |
|---|---|---|
| **Comportamiento** | ¿Qué *hace* el script? | Descarga contenido remoto (B01) |
| **Técnica de ofuscación** | ¿Cómo *oculta* lo que hace? | Codificación Base64, concatenación de cadenas, acentos graves |
| **Clasificación de maliciosidad** | ¿Es *malicioso* en su contexto? | Requiere contexto e intención; no se deriva de un único comportamiento |

Esta taxonomía cubre **solo comportamientos**. Un script puede tener varios comportamientos; uno benigno puede presentar los mismos que uno malicioso. La ofuscación no es por sí misma un comportamiento, salvo cuando el script ejecuta contenido decodificado (B08).

## 2. Reglas generales de etiquetado

- La etiqueta se asigna por **evidencia observable en el código** (original o recuperado estáticamente), no por suposición sobre la intención.
- Cada etiqueta debe poder justificarse citando uno o más fragmentos concretos.
- La mera mención de un término en un comentario o una cadena no utilizada no es suficiente.
- Se mapean técnicas MITRE ATT&CK a modo orientativo; la correspondencia exacta se validará en la integración opcional.

---

## B01 — Descarga de contenido remoto

- **Definición:** el script obtiene datos o archivos desde un recurso remoto (HTTP/HTTPS, FTP, SMB) para guardarlos o usarlos.
- **Evidencias conceptuales:** uso de `Invoke-WebRequest`, `Invoke-RestMethod`, `Start-BitsTransfer`, `System.Net.WebClient` con métodos `DownloadString`/`DownloadFile`/`DownloadData`; URL que apunta a un recurso remoto.
- **Condiciones para asignar:** existe una llamada de descarga alcanzable cuyo origen es remoto.
- **Evidencia insuficiente:** una URL aislada en una cadena o comentario sin operación de descarga asociada; la creación de un objeto `WebClient` sin uso.
- **Usos legítimos:** instaladores, actualizadores, scripts de aprovisionamiento.
- **ATT&CK orientativo:** T1105 Ingress Tool Transfer.

## B02 — Ejecución dinámica de código

- **Definición:** el script construye o carga código en tiempo de ejecución y lo ejecuta.
- **Evidencias conceptuales:** `Invoke-Expression` / `iex`, `[ScriptBlock]::Create(...)` seguido de invocación, operador de llamada `&` sobre contenido construido, carga de ensamblados en memoria (`[Reflection.Assembly]::Load`), `Add-Type` con código fuente.
- **Condiciones para asignar:** el contenido ejecutado se genera, recupera o transforma en tiempo de ejecución.
- **Evidencia insuficiente:** invocar un cmdlet o script local con nombre literal y fijo; la presencia de la palabra `iex` dentro de un comentario.
- **Usos legítimos:** frameworks de automatización, módulos que generan funciones, plantillas.
- **ATT&CK orientativo:** T1059.001 PowerShell; T1620 Reflective Code Loading.

## B03 — Persistencia

- **Definición:** el script establece un mecanismo para ejecutarse de nuevo tras reinicios o inicios de sesión.
- **Evidencias conceptuales:** escritura en claves `Run`/`RunOnce` del registro, creación de tareas programadas (`Register-ScheduledTask`, `schtasks /create`), creación de servicios, suscripciones WMI permanentes, archivos en carpetas de inicio, modificación de perfiles de PowerShell.
- **Condiciones para asignar:** existe una operación de escritura o registro que configura una ejecución futura.
- **Evidencia insuficiente:** solo leer o enumerar tareas o claves `Run`.
- **Usos legítimos:** software de gestión, agentes de monitoreo, tareas de mantenimiento.
- **ATT&CK orientativo:** T1547.001 Registry Run Keys; T1053.005 Scheduled Task; T1546.003 WMI Event Subscription.

## B04 — Modificación de defensas

- **Definición:** el script desactiva, debilita o evade mecanismos de seguridad o registro.
- **Evidencias conceptuales:** `Set-MpPreference` desactivando protecciones o añadiendo exclusiones, cambios de política de ejecución con el fin de eludirla, manipulación de AMSI, desactivación de registro de scripts, detención de servicios de seguridad, borrado de registros de eventos.
- **Condiciones para asignar:** existe una operación que modifica el estado de un control de seguridad.
- **Evidencia insuficiente:** consultar el estado de Defender o de la política de ejecución; el parámetro `-ExecutionPolicy Bypass` en sí solo se registra, pero debe evaluarse en contexto antes de etiquetar.
- **Usos legítimos:** administración de endpoints, configuración de laboratorios, despliegue de software corporativo.
- **ATT&CK orientativo:** T1562.001 Disable or Modify Tools; T1070.001 Clear Windows Event Logs.

## B05 — Reconocimiento del sistema

- **Definición:** el script recopila información sobre el host, usuarios, red local o software instalado.
- **Evidencias conceptuales:** `Get-ComputerInfo`, `Get-CimInstance`/`Get-WmiObject` sobre clases del sistema, `whoami`, `Get-Process`, `Get-Service`, enumeración de usuarios o grupos, `ipconfig`, `Get-NetIPConfiguration`, enumeración de productos de seguridad.
- **Condiciones para asignar:** el script consulta información del entorno y la almacena, procesa o transmite.
- **Evidencia insuficiente:** leer una única variable de entorno para construir una ruta (p. ej. `$env:TEMP`).
- **Usos legítimos:** inventario, diagnóstico, soporte técnico.
- **ATT&CK orientativo:** T1082 System Information Discovery; T1033 System Owner/User Discovery; T1057 Process Discovery.

## B06 — Comunicación de red

- **Definición:** el script establece comunicación de red distinta de una descarga puntual: envío de datos, conexiones persistentes o canales de control.
- **Evidencias conceptuales:** `System.Net.Sockets.TCPClient`, peticiones `POST` con datos del sistema, bucles de consulta periódica a un servidor, resolución DNS usada como canal, `Send-MailMessage` con datos recopilados.
- **Condiciones para asignar:** existe una conexión de red explícita y su propósito no se agota en B01.
- **Evidencia insuficiente:** una dirección IP o dominio aislado; un `Test-Connection` de diagnóstico (se evalúa en contexto).
- **Usos legítimos:** telemetría, integración con API, monitoreo.
- **ATT&CK orientativo:** T1071 Application Layer Protocol; T1041 Exfiltration Over C2 Channel.

## B07 — Acceso a información de credenciales

- **Definición:** el script intenta obtener credenciales, secretos o material de autenticación.
- **Evidencias conceptuales:** acceso a la memoria de LSASS, lectura de colmenas SAM/SECURITY, extracción de credenciales de navegadores o del Administrador de credenciales, `Get-Credential` usado para capturar y enviar, búsqueda de archivos con contraseñas, invocación de herramientas conocidas de volcado.
- **Condiciones para asignar:** existe una operación orientada a leer o extraer material de credenciales.
- **Evidencia insuficiente:** pedir credenciales al usuario para autenticarse legítimamente en un recurso (`Get-Credential` pasado a `-Credential`); variables llamadas `password` sin acceso a almacenes.
- **Usos legítimos:** auditorías de seguridad autorizadas, gestión de secretos, migraciones.
- **ATT&CK orientativo:** T1003 OS Credential Dumping; T1555 Credentials from Password Stores.

## B08 — Ejecución de contenido codificado

- **Definición:** el script decodifica contenido (Base64, compresión, XOR, cadenas de caracteres) y lo ejecuta.
- **Evidencias conceptuales:** `-EncodedCommand` / `-enc`, `[Convert]::FromBase64String` seguido de ejecución, `IO.Compression.DeflateStream`/`GzipStream` cuyo resultado se invoca, reconstrucción por `[char]` y ejecución.
- **Condiciones para asignar:** existe una cadena de decodificación cuyo resultado alcanza un punto de ejecución. Normalmente coexiste con B02.
- **Evidencia insuficiente:** decodificar Base64 para leer datos que no se ejecutan (p. ej., una imagen o un certificado).
- **Usos legítimos:** empaquetado de scripts, evitar problemas de escape en líneas de comando.
- **ATT&CK orientativo:** T1027 Obfuscated Files or Information; T1140 Deobfuscate/Decode Files or Information.

---

## 3. Pendientes de revisión

- Validar los criterios con muestras reales del conjunto de desarrollo.
- Decidir si B01 y B06 se mantienen separados o se fusionan según su separabilidad práctica.
- Definir el tratamiento de comportamientos condicionales (código alcanzable solo bajo ciertas condiciones).
- Confirmar el mapeo ATT&CK con los datos STIX.
