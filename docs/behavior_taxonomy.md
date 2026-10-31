# Taxonomía de comportamientos

> **Versión provisional v0.2 (B01–B07).** El catálogo de siete comportamientos funcionales está aprobado como punto de partida. Los criterios de cada categoría deben validarse con el conjunto de desarrollo y congelarse antes de etiquetar el conjunto de prueba. Los ejemplos son conceptuales y no constituyen código ejecutable.
>
> **Cambios respecto a v0.1:** B08 (ejecución de contenido codificado) se retiró del catálogo; B02 se restringió a la ejecución dinámica funcional; se fijó la regla B01/B06; B07 deja de asignarse por el simple uso de `Get-Credential`.

## 1. Tres ejes independientes

| Eje | Pregunta que responde | Dónde se registra | Ejemplo |
|---|---|---|---|
| **Comportamiento** | ¿Qué *hace* el código? | `behavior_labels` + anotaciones de evidencia | Descarga contenido remoto (B01) |
| **Técnica de ofuscación** | ¿Cómo *oculta* lo que hace? | `obfuscation_techniques`, `added_operations` | Base64 con `-EncodedCommand`, concatenación de literales |
| **Valoración de riesgo** | ¿Qué riesgo se puede *sustentar* en su contexto? | `scenario_type`, `risk_label`, `risk_basis` | `suspicious` por persistencia sin propósito claro |

Esta taxonomía cubre **solo comportamientos**. Un script puede tener varios; uno legítimo puede presentar los mismos que uno abusivo. La evaluación principal del proyecto se centra en este eje; la valoración de riesgo es un análisis secundario ([methodology.md](methodology.md)).

## 2. Reglas generales de etiquetado

1. Se etiqueta lo que el código **hace**, por evidencia observable en el código original o en contenido recuperado estáticamente, no lo que podría hacer ni la intención supuesta.
2. Cada etiqueta se justifica con al menos una evidencia localizada (línea y fragmento literal), registrada en el archivo de anotaciones ([dataset_selection_plan.md](dataset_selection_plan.md#6-evidencias-y-anotaciones)).
3. La mención de un término en un comentario o en una cadena que no se usa **no** es evidencia.
4. Las etiquetas de referencia se asignan sobre el **original (`v0`)**. Una variante solo hereda esas etiquetas cuando su equivalencia funcional ha sido revisada ([dataset_selection_plan.md](dataset_selection_plan.md#3-equivalencia-funcional-entre-original-y-variantes)).
5. Las operaciones introducidas exclusivamente por la ofuscación (p. ej., envoltorios `Invoke-Expression`) **no** generan comportamientos nuevos; se registran en `added_operations`.
6. Las técnicas MITRE ATT&CK indicadas son orientativas; el mapeo se validará en la integración opcional con STIX.

## 3. Registro de la ofuscación y del contenido codificado

La antigua categoría B08 describía **cómo** se oculta el código, no **qué** hace: la variante Base64 de un script de inventario habría tenido B08 y el original no. Por eso:

- La codificación se registra como técnica de ofuscación en `obfuscation_techniques` (`OT-B64-ENCCMD`, `OT-B64-INLINE`, etc.; ver la lista de códigos en [dataset_selection_plan.md](dataset_selection_plan.md#41-códigos-de-técnicas-de-ofuscación)).
- Si el decodificado y la ejecución **forman parte de la lógica funcional del original** (p. ej., una simulación de *stager* que decodifica y ejecuta un bloque como parte de su escenario), el comportamiento se etiqueta como **B02**, y la codificación se registra también como técnica presente en `v0`.
- El identificador **B08 queda retirado** y no se reutilizará para otra categoría en esta versión, para evitar confusión con anotaciones previas.

---

## B01 — Descarga de contenido remoto

- **Definición:** el script obtiene datos o archivos desde un recurso remoto (HTTP/HTTPS, FTP, SMB) para guardarlos o usarlos.
- **Evidencias conceptuales:** `Invoke-WebRequest` (incluido `-OutFile`), `Invoke-RestMethod` con método GET, `Start-BitsTransfer`, `System.Net.WebClient` con `DownloadString`/`DownloadFile`/`DownloadData`, alias `curl`/`wget` con URL.
- **Condiciones para asignar:** existe una llamada de descarga alcanzable cuyo origen es remoto, literal o recuperable estáticamente.
- **Evidencia insuficiente:** una URL aislada en una cadena o comentario sin operación de descarga; la creación de un `WebClient` que no se usa.
- **Usos legítimos:** instaladores, actualizadores, aprovisionamiento, descarga de reportes.
- **Relación con B06:** si la única actividad de red es la descarga, se asigna **solo B01**.
- **ATT&CK orientativo:** T1105 Ingress Tool Transfer.

## B02 — Ejecución dinámica de código como parte de la lógica funcional

- **Definición:** el script original construye, recupera o carga código en tiempo de ejecución y lo ejecuta **como parte de su propósito funcional**.
- **Evidencias conceptuales:** `Invoke-Expression`/`iex` sobre contenido descargado o construido por la lógica del script (p. ej., `IEX (New-Object Net.WebClient).DownloadString(...)`), `[ScriptBlock]::Create(...)` con invocación, operador `&` sobre una cadena construida, `[Reflection.Assembly]::Load`, `Add-Type` con código fuente.
- **Condiciones para asignar:** la ejecución dinámica está presente en el **original** y el contenido ejecutado se genera, recupera o transforma en tiempo de ejecución.
- **Evidencia insuficiente:**
  - Envoltorios `IEX` u operadores de invocación **añadidos por una herramienta de ofuscación**. Se registran en `added_operations` (p. ej., `EXEC_WRAPPER_IEX`) y no generan B02.
  - Invocar un cmdlet o un script local con nombre literal fijo.
  - La palabra `iex` en un comentario.
- **Usos legítimos:** frameworks de automatización, módulos que generan funciones, instaladores de una línea.
- **ATT&CK orientativo:** T1059.001 PowerShell; T1620 Reflective Code Loading.

## B03 — Persistencia

- **Definición:** el script establece un mecanismo para volver a ejecutarse tras reinicios o inicios de sesión.
- **Evidencias conceptuales:** escritura en claves `Run`/`RunOnce` (`HKCU`/`HKLM`), `Register-ScheduledTask`, `schtasks /create`, creación de servicios, suscripciones WMI permanentes, archivos en carpetas de inicio, modificación de perfiles de PowerShell.
- **Condiciones para asignar:** existe una operación de escritura o registro que configura una ejecución futura, aunque apunte a una ruta inexistente.
- **Evidencia insuficiente:** solo leer o enumerar tareas o claves `Run` (eso es B05).
- **Usos legítimos:** agentes de gestión y monitoreo, tareas de mantenimiento.
- **ATT&CK orientativo:** T1547.001 Registry Run Keys; T1053.005 Scheduled Task; T1546.003 WMI Event Subscription.

## B04 — Modificación de mecanismos de defensa

- **Definición:** el script desactiva, debilita o evade mecanismos de seguridad o de registro.
- **Evidencias conceptuales:** `Set-MpPreference -Disable*`, `Add-MpPreference -ExclusionPath`, manipulación de AMSI, desactivación del registro de scripts, desactivación del firewall, detención de servicios de seguridad, borrado de logs (`wevtutil cl`, `Clear-EventLog`).
- **Condiciones para asignar:** existe una operación que cambia el estado de un control de seguridad.
- **Evidencia insuficiente:** consultar el estado de Defender o de la política de ejecución; `-ExecutionPolicy Bypass` en el lanzador (parámetro de la ejecución actual, no modifica una defensa persistente; se anota en `notes`).
- **Usos legítimos:** administración de endpoints, laboratorios, despliegues corporativos.
- **ATT&CK orientativo:** T1562.001 Disable or Modify Tools; T1070.001 Clear Windows Event Logs.

## B05 — Reconocimiento del sistema

- **Definición:** el script recopila información sobre el host, los usuarios, la red local o el software instalado.
- **Evidencias conceptuales:** `Get-Process`, `Get-Service`, `Get-ComputerInfo`, `systeminfo`, `whoami`, `Get-CimInstance Win32_*`, `net user`, `Get-ADUser`, `ipconfig`, `Get-NetIPConfiguration`, enumeración de productos de seguridad.
- **Condiciones para asignar:** el script consulta información del entorno y la almacena, procesa, muestra o transmite.
- **Evidencia insuficiente:** leer una variable de entorno para construir una ruta (p. ej., `$env:TEMP`).
- **Usos legítimos:** inventario, diagnóstico, soporte. Es frecuente en scripts benignos, lo que permite medir si el sistema confunde comportamiento con riesgo.
- **ATT&CK orientativo:** T1082 System Information Discovery; T1033 System Owner/User Discovery; T1057 Process Discovery.

## B06 — Comunicación de red distinta de una descarga

- **Definición:** el script establece comunicación de red **que no se agota en una descarga**: envío o subida de datos, conexiones con sockets, sesiones remotas, canales de control o pruebas de conectividad.
- **Evidencias conceptuales:** `System.Net.Sockets.TcpClient`, `Invoke-RestMethod`/`Invoke-WebRequest` con `POST`/`PUT` de datos, `Test-NetConnection`, `Enter-PSSession`/`Invoke-Command -ComputerName`, consultas DNS usadas como canal, listeners, `Send-MailMessage`.
- **Condiciones para asignar:** existe una comunicación de red explícita, independiente de las descargas del script.
- **Regla con B01:** si la única actividad de red identificada es una descarga, se asigna **B01 y no B06**. Si además hay otra comunicación independiente (p. ej., descarga un archivo y luego envía datos a otro servidor), **B01 y B06 coexisten**.
- **Evidencia insuficiente:** una IP o un dominio aislado sin operación de red; crear un objeto de credenciales (`Get-Credential`, `New-Object PSCredential`) sin una operación de red explícita.
- **Usos legítimos:** telemetría, integración con API, administración remota, monitoreo.
- **Pendiente:** decidir si las llamadas de cmdlets de gestión de nube (p. ej., módulo Az) cuentan como B06 o se tratan como operación administrativa sin etiqueta (ver [dataset_audit.md](dataset_audit.md)).
- **ATT&CK orientativo:** T1071 Application Layer Protocol; T1041 Exfiltration Over C2 Channel; T1021.006 Windows Remote Management.

## B07 — Acceso a información de credenciales

- **Definición:** el script accede a material de credenciales **almacenado o perteneciente a terceros**, o intenta extraerlo.
- **Se distinguen tres situaciones:**

  | Situación | Ejemplo conceptual | ¿B07? |
  |---|---|---|
  | **Autenticación administrativa** | `Get-Credential` cuyo resultado se pasa a `-Credential` para conectarse a un recurso | **No**. `Get-Credential` por sí solo no implica B07 ni B06. Si el script además realiza una operación de red explícita (p. ej., `Invoke-Command -ComputerName`), esa operación se evalúa por separado como posible B06 |
  | **Acceso a información de credenciales** | Leer el Administrador de credenciales, archivos con contraseñas, almacenes del navegador, `Get-StoredCredential`, buscar contraseñas en archivos | **Sí** |
  | **Extracción o volcado** | Acceso a la memoria de LSASS, copia de las colmenas `SAM`/`SECURITY`, invocación de herramientas de volcado | **Sí** (se indica en la nota de la evidencia) |

- **Condiciones para asignar:** existe una operación orientada a leer o extraer material de credenciales que el script no recibió legítimamente para autenticarse. Una captura con `Get-Credential` cuyo resultado se guarda o se transmite a terceros sí es B07 (y posiblemente B06).
- **Evidencia insuficiente:** `Get-Credential` usado solo para autenticarse (tampoco justifica por sí mismo una valoración de riesgo sospechosa); variables llamadas `password` sin acceso a almacenes.
- **Usos legítimos:** auditorías autorizadas, gestión de secretos, migraciones.
- **ATT&CK orientativo:** T1003 OS Credential Dumping; T1555 Credentials from Password Stores; T1056.002 GUI Input Capture.

---

## 4. Pendientes de revisión

- Validar los criterios con los scripts del conjunto de desarrollo antes de congelarlos.
- Decidir el tratamiento de las llamadas a API de gestión en la nube respecto de B06.
- Definir el tratamiento de comportamientos condicionales (código alcanzable solo bajo ciertas condiciones).
- Confirmar el mapeo ATT&CK con los datos STIX.
