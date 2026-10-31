# Fuentes de datos candidatas

> **Estado:** las fuentes se revisaron **documentalmente** en la Fase 0A (README, licencias, estructura y metadatos públicos). **No se ha descargado, clonado ni ejecutado ninguna muestra ni herramienta**, y ninguna muestra externa se incorpora a este repositorio. El análisis detallado, con el nivel de verificación de cada hallazgo, está en [dataset_audit.md](dataset_audit.md); el uso previsto de cada fuente, en [dataset_selection_plan.md](dataset_selection_plan.md).

## Principios generales

- Un script **no ofuscado no es necesariamente benigno**.
- Un script proveniente de un repositorio ofensivo o de investigación **no es necesariamente malicioso**.
- Las etiquetas de origen (p. ej., "malicioso"/"benigno", "ofuscado"/"no ofuscado") no equivalen a etiquetas de comportamiento; estas se asignan según la [taxonomía B01–B07](behavior_taxonomy.md).
- Un repositorio público no concede por sí mismo derechos de redistribución, y la licencia del código de una herramienta no cubre automáticamente los datos que referencia.
- Toda muestra externa se maneja fuera del repositorio (`datasets/raw/`, `datasets/external/`, `datasets/quarantine/` o `datasets/private/`, ignorados por Git), en un entorno aislado y sin ejecutarla. Ver [security.md](security.md).
- De cada muestra utilizada se registra en el manifiesto (`datasets/metadata/`): hash SHA-256, fuente, versión o commit de la fuente, licencia y etiquetas.

## Resumen

| Fuente | Qué es | Licencia | Limitación principal | Uso previsto |
|---|---|---|---|---|
| [Revoke-Obfuscation](https://github.com/danielbohannon/Revoke-Obfuscation) | Detector de ofuscación con etiquetas ofuscado/no ofuscado sobre un corpus externo | Apache 2.0 (código); corpus sin licencia declarada | Sus etiquetas indican ofuscación, no maliciosidad ni comportamiento | Referencia metodológica; benignos opcionales |
| [Malicious-PowerShell-Dataset (Fa2y)](https://github.com/Fa2y/Malicious-PowerShell-Dataset) | Muestras declaradas maliciosas, de repositorios ofensivos y sandboxes | Sin licencia visible | Etiqueta implícita por procedencia, con ruido; emparejamiento original/ofuscado no garantizado | Metadatos; ≤ 6 scripts revisados en entorno aislado (opcional) |
| [Invoke-Obfuscation](https://github.com/danielbohannon/Invoke-Obfuscation) | Herramienta de transformación, no dataset etiquetado | Apache 2.0 | Añade envoltorios IEX; la mayoría de técnicas no son resolubles estáticamente | Generador del estrato no soportado, en entorno aislado |
| [MPSD](https://github.com/das-lab/mpsd) | Muestras maliciosas, benignas y mixtas de un artículo académico | Sin licencia visible (pendiente de confirmar) | Etiquetas binarias declaradas por los autores, no B01–B07 | Referencia; benignos opcionales |
| [Azure-Samples/azure-docs-powershell-samples](https://github.com/Azure-Samples/azure-docs-powershell-samples) | Ejemplos administrativos de Azure PowerShell de la documentación de Microsoft | MIT | Orientados a la nube; poca correspondencia con comportamientos del host | Candidata para administrativos legítimos (S1) |
| [MITRE ATT&CK STIX](https://github.com/mitre-attack/attack-stix-data) | Representación de ATT&CK en STIX 2.1 | Ver términos de uso de MITRE | El mapeo comportamiento → técnica no es uno a uno; hay que fijar la versión | Mapeo opcional (`threat_intelligence`) |

## Pendiente de verificar (Fase 0B)

- Contenido real, volumen, duplicados y casi-duplicados de las fuentes que se usen, en entorno aislado.
- Relación entre los porcentajes de ofuscación declarados por Fa2y y emparejamiento de sus variantes.
- Licencias no declaradas (corpus de Revoke-Obfuscation, Fa2y, MPSD).
- Número y tamaño de los scripts de Azure-Samples.
- Versión de ATT&CK a utilizar y si los datos STIX se versionan o se descargan localmente.
