# Fuentes de datos candidatas

> **Ninguna de estas fuentes ha sido descargada, inspeccionada ni validada todavía.** La información sobre su contenido es preliminar y debe confirmarse en la Fase 0. Ninguna muestra externa se incorpora a este repositorio.

## Principios generales

- Un script **no ofuscado no es necesariamente benigno**.
- Un script proveniente de un repositorio ofensivo o de investigación **no es necesariamente malicioso**.
- Las etiquetas de origen (p. ej., "malicioso"/"benigno", "ofuscado"/"no ofuscado") no equivalen a etiquetas de comportamiento; estas se asignan según la [taxonomía](behavior_taxonomy.md).
- Toda muestra externa se maneja fuera del repositorio (`datasets/raw/`, `datasets/external/`, `datasets/quarantine/` o `datasets/private/`, ignorados por Git), en un entorno aislado y sin ejecutarla. Ver [security.md](security.md).
- De cada muestra utilizada se registra en `datasets/metadata/`: hash SHA-256, fuente, versión/commit de la fuente, licencia y etiquetas.

---

## 1. Revoke-Obfuscation

- **URL:** https://github.com/danielbohannon/Revoke-Obfuscation
- **Propósito:** herramienta de detección de ofuscación en PowerShell basada en características del AST, publicada junto con investigación sobre detección de scripts ofuscados.
- **Utilidad potencial:** posible fuente de scripts etiquetados como ofuscados/no ofuscados; referencia de características para el motor estático; línea de comparación conceptual.
- **Datos esperados:** scripts PowerShell y etiquetas de ofuscación (por confirmar si los datos completos están en el repositorio o deben obtenerse aparte).
- **Riesgos metodológicos:** las etiquetas indican ofuscación, no comportamiento ni maliciosidad; antigüedad del corpus; posible solapamiento con datos de entrenamiento del LLM.
- **Pendiente de verificar:** disponibilidad real del corpus, formato, licencia, volumen, presencia de código malicioso activo.

## 2. Malicious-PowerShell-Dataset

- **URL:** https://github.com/Fa2y/Malicious-PowerShell-Dataset
- **Propósito:** recopilación de scripts PowerShell presentada como maliciosa, orientada a investigación de detección.
- **Utilidad potencial:** fuente de scripts con comportamientos reales para el conjunto experimental, previo etiquetado por comportamiento.
- **Datos esperados:** scripts PowerShell, posiblemente acompañados de metadatos o etiquetas binarias (por confirmar).
- **Riesgos metodológicos:** contiene previsiblemente malware real (manejo solo en entorno aislado); duplicados y variantes de una misma familia que pueden contaminar la separación desarrollo/evaluación; etiquetas sin criterios documentados; procedencia heterogénea.
- **Pendiente de verificar:** licencia y condiciones de uso, procedencia, formato, duplicados, distribución de comportamientos, criterio de etiquetado.

## 3. Invoke-Obfuscation

- **URL:** https://github.com/danielbohannon/Invoke-Obfuscation
- **Propósito:** framework de ofuscación de PowerShell, usado para investigación y para probar capacidades de detección.
- **Utilidad potencial:** referencia de técnicas de ofuscación que el motor estático debe reconocer; posible generación controlada de pares (original ↔ ofuscado) a partir de scripts **inertes** para evaluar la recuperación de código.
- **Datos esperados:** código de la herramienta, no un dataset.
- **Riesgos metodológicos:** ejecutar la herramienta implica ejecutar PowerShell (solo en entorno aislado y sobre scripts inertes); las ofuscaciones generadas pueden no representar la distribución real de ataques; riesgo de sesgar el motor estático hacia una sola herramienta.
- **Pendiente de verificar:** licencia, técnicas soportadas, procedimiento seguro de generación y si su uso es necesario o basta con documentar las técnicas.

## 4. MITRE ATT&CK STIX Data

- **URL:** https://github.com/mitre-attack/attack-stix-data
- **Propósito:** representación oficial de ATT&CK en formato STIX 2.1.
- **Utilidad potencial:** mapeo opcional de comportamientos a técnicas (módulo `threat_intelligence`); vocabulario de referencia para la taxonomía.
- **Datos esperados:** archivos JSON STIX 2.1 con tácticas, técnicas, subtécnicas y relaciones, versionados por release de ATT&CK.
- **Riesgos metodológicos:** el mapeo comportamiento → técnica no es uno a uno; cambios entre versiones de ATT&CK (fijar versión).
- **Pendiente de verificar:** versión a utilizar, tamaño del archivo, si se versiona en el repo o se descarga localmente, licencia y atribución.

---

## Fuentes de muestras benignas

El diseño experimental requiere también scripts benignos (incluidos benignos que presenten comportamientos como B01 o B05). Fuentes candidatas a evaluar en la Fase 0: scripts administrativos de repositorios públicos con licencia abierta, documentación oficial y scripts escritos por el equipo. Ninguna ha sido seleccionada todavía.
