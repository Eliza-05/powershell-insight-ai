# Fase 4 — independencia: evidencia y revisión pendiente

**Ninguna referencia o independencia semántica está aprobada automáticamente.**

Audit local: 567 textos previos únicos y 449 vistas estructurales únicas. Cero duplicados exactos o programas completos normalizados equivalentes encontrados.

El inventario se limita a archivos presentes en el manifiesto anterior a esta preparación. Incluye selección, desarrollo, diagnósticos y literales de pruebas; excluye los nuevos tests Fase 4 y los borradores para evitar autocontaminación del audit. No se leyeron muestras raw, externas, privadas o en cuarentena.

Se ignoran comentarios y se normalizan variables, strings y números. También se inspeccionan vistas de texto recuperadas determinísticamente para no ocultar un base antiguo bajo otro wrapper. Los scores de secuencia de tokens son cribado, no equivalencia semántica.

| ID | Prior más cercano | Similitud estructural | Diferencia lógica propuesta por el autor; pendiente de revisión |
|---|---|---:|---|
| F4-01 | `datasets/safe_samples/pilot_v2/selection/V2-S04.ps1.txt` | 0.500 | HttpClient asíncrono → awaiter → bytes → longitud; sin cargador ni llamada de ejecución. |
| F4-02 | `datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt` | 0.578 | DownloadData → mismo array de bytes → Assembly.Load; metadatos de ensamblado, no IEX sobre texto. |
| F4-03 | `experiments/demo_deobfuscation.py:literal` | 0.500 | Herramienta nativa de tareas con trigger logon y destino remoto explícito; credencial literal ficticia, no extracción. |
| F4-04 | `experiments/demo_deobfuscation.py:literal` | 0.762 | Borrado de historial de logging por canal y host, no exclusión Defender ni cambio de firewall. |
| F4-05 | `datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt` | 0.605 | Consulta de eventos → serialización → cuerpo exacto de PUT vía UploadString; no inventario IP+POST. |
| F4-06 | `datasets/safe_samples/pilot_v2/selection/V2-S04.ps1.txt` | 0.625 | Import-Clixml de almacén local ficticio → GetNetworkCredential.Password; no despacho de handler desconocido. |
| F4-07 | `datasets/safe_samples/pilot_v2/selection/V2-S04.ps1.txt` | 0.591 | Código C# armado fuera del bloque, compilador dentro de ScriptBlock no llamado; solo se consulta longitud del texto. |
| F4-08 | `datasets/safe_samples/pilot_v2/selection/V2-S04.ps1.txt` | 0.318 | DynamicMethod → generador IL → carga de dos argumentos/suma/retorno → Invoke; no ScriptBlock.Create ni IEX ni texto Write-Output. |
| F4-09 | `datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt` | 0.257 | Bóveda → Credential de WMI → filtro/consumidor/binding permanente con referencias de objetos explícitas; distinta de tarea programada. |
| F4-10 | `datasets/safe_samples/pilot/PILOT-P6.ps1.txt` | 0.300 | Deshabilita logging futuro de un canal ficticio; contraste con borrado histórico remoto, sin red. |
| F4-11 | `datasets/safe_samples/pilot_v2/selection/V2-S13.ps1.txt` | 0.424 | Inventario de dos mecanismos de configuración sin registro ni cambio; negativo difícil B03/B04. |
| F4-12 | `datasets/safe_samples/pilot_v2/references/V2-S16_decoded.ps1.txt` | 0.667 | Captura interactiva → Credential de remoting fijo → bloque literal; no lectura de almacén ni evaluación de texto construido. |
| F4-13 | `datasets/safe_samples/pilot_v2/selection/V2-S03.ps1.txt` | 0.585 | Extrae y transforma nombres desde documentación literal; no ejecuta los comandos que reconoce. |
| F4-14 | `datasets/safe_samples/pilot_v2/selection/V2-S12.ps1.txt` | 0.362 | Bytes constantes → GZip en memoria → Base64 de salida; no decodificación ni evaluación de comandos. |
| F4-15 | `datasets/safe_samples/pilot_v2/development/V2-D24.ps1.txt` | 0.372 | Operación web parametrizada: no se conoce destino/método/cuerpo para distinguir descarga de envío. |
| F4-16 | `datasets/safe_samples/pilot/PILOT-P7.ps1.txt` | 0.338 | Inventario de caché DNS local conocido y selección de callback por tabla externa; conjunto interno no determinable. |

## Puntos que debe revisar personalmente el responsable

- F4-08 inicialmente repetía el patrón exterior de ScriptBlock.Create de V2-S04 (0,939). Antes de cualquier respuesta B/C se sustituyó por generación de IL, ejecución de una suma local y una relación de datos distinta. El nuevo vecino más próximo tiene similitud 0,318. Los borradores anteriores se conservaron; no son parte del candidato actual.
- F4-04 comparte el esqueleto asignación/concatenación con un demo previo que solo mostraba texto; la operación nueva es Clear-EventLog remoto. Confirmar que esa diferencia es funcional, no solo nominal.
- F4-12 comparte Get-Credential con controles anteriores, pero enlaza la credencial a remoting y no a un proceso local o mera solicitud. Confirmar el nuevo flujo y la exclusión B07.
- F4-02/F4-05 comparten construcción de URL y WebClient; el primero descarga bytes y carga un ensamblado, el segundo consulta eventos y envía su JSON por PUT. Revisar posible dependencia residual, sin asumir independencia por API distinta.
- F4-06/F4-07 comparten asignación de texto, pero difieren entre lectura material de credencial CLIXML y compilación almacenada nunca invocada. La similitud léxica por boilerplate no decide por sí sola la familia.
- Los dos mecanismos de logging F4-04/F4-10 se agruparon conservadoramente en audit-control. Otras agrupaciones solo pueden cambiarse antes de congelar, con justificación personal.

## Límites

No es posible demostrar independencia lógica completa mediante hash o normalización. Las referencias y la novedad deben revisarse personalmente antes de sellar. Los mismos autores conocían los fallos históricos, las primitivas B01–B07 siguen siendo compartidas y el corpus no es una muestra aleatoria. No se afirma independencia del preentrenamiento de Qwen ni generalización a malware real.

El archivo [independence_audit.json](../artifacts/phase4_preparation/proposal/independence_audit.json) conserva los tres vecinos más cercanos por caso y las banderas de similitud interna. Las observaciones de este documento son asistidas por IA y no constituyen una revisión humana independiente.
