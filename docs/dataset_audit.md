# Auditoría de fuentes de datos — Fase 0A

**Proyecto:** PowerShell Insight AI
**Fecha de la auditoría:** 2026-10-29
**Alcance:** inspección de documentación, README, licencias, estructura de carpetas y metadatos publicados. **No se clonó, descargó ni ejecutó ninguna muestra ni herramienta.**

> **Revisión de la Fase 0A (2026-10-29).** Los hallazgos de las fuentes A, B, C y MPSD provienen de la auditoría original y conservan su nivel de verificación. Esta revisión precisa su interpretación (etiquetas, licencias y emparejamiento) sin añadir verificaciones nuevas sobre ellas. La fuente Azure-Samples se revisó documentalmente en esta revisión. Las referencias a la taxonomía remiten a la versión aprobada B01–B07 ([behavior_taxonomy.md](behavior_taxonomy.md)).

## Convenciones

Cada hallazgo se marca con su nivel de verificación:

- **[COMPROBADO]**: visto directamente en el repositorio, el README o un archivo de metadatos público durante la auditoría.
- **[AUTOR]**: afirmación de los autores (README, paper, white paper) que no podemos verificar sin inspeccionar los datos.
- **[PENDIENTE]**: requiere verificación en un entorno aislado y autorizado (Fase 0B) o consulta adicional.

Principios transversales:

- **"Ofuscado" no implica "malicioso" y "no ofuscado" no implica "benigno".**
- **Una procedencia ofensiva no prueba maliciosidad** y una procedencia administrativa no prueba inocuidad.
- Ninguna etiqueta de las fuentes se usará como etiqueta de comportamiento B01–B07 sin revisión humana.

## Licencias y redistribución

- **Que un repositorio sea público no concede derechos generales de redistribución.** Sin licencia explícita, la regla por defecto es que no hay permiso para redistribuir.
- La licencia del **código** de una herramienta no se extiende automáticamente a los **datos** que referencia o recopila (corpus externos, muestras de sandboxes, scripts de terceros).
- Regla del proyecto: de las fuentes externas solo se versionan metadatos, hashes y referencias. Cuando se adapte un script con licencia permisiva, se conserva la atribución y la licencia de origen en el manifiesto (`source_license`, `provenance_notes`).

---

## Fuente A — Revoke-Obfuscation

**URL:** https://github.com/danielbohannon/Revoke-Obfuscation
**Documentación clave:** [README](https://github.com/danielbohannon/Revoke-Obfuscation), [DataScience/README.md](https://github.com/danielbohannon/Revoke-Obfuscation/blob/master/DataScience/README.md), [white paper Black Hat 2017](https://blackhat.com/docs/us-17/thursday/us-17-Bohannon-Revoke-Obfuscation-PowerShell-Obfuscation-Detection-And%20Evasion-Using-Science-wp.pdf)

### Qué ofrece
- **[COMPROBADO]** Un framework PowerShell (v3.0+) que **detecta ofuscación**, no maliciosidad. Extrae características del AST y las compara con un vector de pesos entrenado por regresión logística.
- **[COMPROBADO]** Carpeta `DataScience/` con archivos `*-labeledData.csv`. Se observaron al menos `IseSteroids-obfuscation-labeledData.csv` (789 líneas), `PoshCode-obfuscation-labeledData.csv` (3405 líneas) y `TechNet-obfuscation-labeledData.csv` (1540 líneas). **[PENDIENTE]** listado completo de los CSV.
- **[COMPROBADO]** Los CSV tienen una columna `Path` (ruta relativa dentro del corpus) y una columna `Label` (`1` = ofuscado, `0` = no ofuscado). **No contienen el código**, solo referencias al corpus.
- **[COMPROBADO]** El corpus completo (PowerShellCorpus) se distribuye aparte en `http://aka.ms/PowerShellCorpus`.

### Composición del corpus
- **[AUTOR]** 408.665 scripts de 28.748 autores, unos 4 GB sin comprimir.
- **[AUTOR]** Fuentes: PowerShell Gallery, PoshCode, GitHub, GitHub Gists y TechNet Script Center, más salidas de tres frameworks de ofuscación: Invoke-CradleCrafter, Invoke-Obfuscation e ISESteroids.
- **[AUTOR]** Los autores advierten que el corpus **no es dirigido**: no representa específicamente malware, ni ofuscación, ni uso administrativo; contiene un poco de todo.

### Etiquetas
- **Las etiquetas indican presencia de ofuscación, no maliciosidad ni comportamiento.** Un `Label = 1` no implica malicioso y un `Label = 0` no implica benigno.
- **[AUTOR]** Unos 7.000 scripts de autores humanos etiquetados manualmente (1.600 como ofuscados) y unos 4.000 generados por frameworks (todos etiquetados como ofuscados).
- **[AUTOR]** Según el white paper, los ofuscados sintéticos son 3.200 de Invoke-Obfuscation, 788 de ISESteroids y 200 de Invoke-CradleCrafter, generados a partir de scripts del propio corpus. También se incluyeron 383 envíos del Underhanded PowerShell Contest.
- **[AUTOR]** Criterio de etiquetado: "¿querríamos que este elemento se revisara durante una respuesta a incidentes?".
- **[AUTOR]** Los propios autores advierten que **usar estas etiquetas para detectar PowerShell malicioso sería un enfoque poco sensato**.

### Licencia
- **[COMPROBADO]** El código del repositorio está bajo **Apache 2.0**.
- Esa licencia cubre el código del framework y **no implica permisos sobre los scripts del corpus externo**.
- **[PENDIENTE]** El corpus no declara una licencia propia en la documentación revisada. Los scripts pertenecen a miles de autores con licencias heterogéneas. Tratarlo como material de investigación y **no redistribuir scripts del corpus en nuestro repositorio**.

### Pares original/ofuscado
- **[PENDIENTE]** Los ~4.000 ofuscados sintéticos se generaron a partir de scripts del corpus, pero la documentación revisada **no describe un mapeo explícito** original → variante. Sin ese mapeo, no sirven como ground truth de recuperación.

### Duplicados y sesgos
- **[PENDIENTE]** Un corpus de esta escala casi seguro contiene duplicados y casi-duplicados (forks, copias entre Gallery, GitHub y Gists). No hay deduplicación documentada.
- Sesgo temporal: los datos son de 2017. Las técnicas de ofuscación actuales pueden no estar representadas.
- El corpus incluye herramientas ofensivas públicas y salidas de ofuscadores, así que **no se puede asumir que los scripts con `Label = 0` sean benignos**.

### Utilidad para el experimento
- **Útil:** fuente candidata de **scripts administrativos reales** para crear originales benignos, siempre tras revisión manual. También sirve de referencia metodológica.
- **No útil:** como fuente de etiquetas de maliciosidad ni de comportamientos, ni como fuente de pares original/ofuscado.
- **Riesgo práctico:** descargar 4 GB de scripts heterogéneos para extraer unos pocos benignos es desproporcionado.

---

## Fuente B — Malicious-PowerShell-Dataset (Fa2y)

**URL:** https://github.com/Fa2y/Malicious-PowerShell-Dataset

### Qué ofrece
- **[COMPROBADO]** Repositorio de scripts PowerShell maliciosos usado en una tesis o investigación sobre detección con deep learning. La cita está marcada como `TODO` en el README.
- **[COMPROBADO]** Estructura de primer nivel:
  - `malicious_samples/`: muestras ensambladas, nombradas `{sha256}.ps1`.
  - `bazaar_out/`, `hybrid_analysis_out/`, `triage_out/`: muestras por fuente.
  - `hybrid_analysis_data.json`, `triage_data.json`: metadatos (IDs, hashes, fechas, nombres de archivo, tipo y tags).
  - Scripts de recolección: `download_mb_samples.py`, `download_triage.py`, `scrape_hybrid_analysis_ui.py`, `scrape_triage.py`.
  - Scripts de ofuscación: `dataset-obfuscator.py` (Chameleon) e `Invoke-ObfuscateRandomFiles.ps1` (Invoke-Obfuscation).

### Procedencia
- **[AUTOR]** Repositorios ofensivos de GitHub, entre ellos Empire, PowerSploit, nishang, PoshC2, BloodHound, mimikittenz, invoke-atomicredteam y PersistenceSniper.
- **[AUTOR]** El dataset público MPSD (Fang, Zhou y Huang).
- **[AUTOR]** Sandboxes en línea: Triage (filtros por troyanos, Metasploit y CobaltStrike), Hybrid Analysis (veredicto malicioso) y Malware Bazaar (tipo PS1).
- **[AUTOR]** La recolección de Hybrid Analysis quedó limitada a unas 200 muestras por un problema del sitio.

### Etiquetas
- **[COMPROBADO]** No hay archivo de etiquetas por muestra. La "etiqueta" es implícita: **todo lo del repositorio se considera malicioso por su procedencia**.
- **[COMPROBADO]** Algunos repositorios de origen son de doble uso o directamente defensivos:
  - **PersistenceSniper** es una herramienta de *hunting* de persistencia, es decir, defensiva.
  - **invoke-atomicredteam** es un framework de pruebas de detección.
  - **BloodHound** es una herramienta de auditoría de Active Directory usada tanto por equipos rojos como azules.

  **Consecuencia:** la etiqueta "malicioso" tiene ruido significativo y no puede usarse como ground truth sin revisión.
- **[COMPROBADO]** No hay etiquetas de comportamiento. Los tags de los JSON de Triage y Hybrid Analysis podrían dar pistas de familia. **[PENDIENTE]** revisar su contenido.

### Ofuscación y pares
- **[AUTOR]** El README dice que se ofuscó **aproximadamente el 25%** de las muestras con Chameleon e Invoke-Obfuscation.
- **[AUTOR]** La descripción de `Invoke-ObfuscateRandomFiles.ps1` dice que se ofuscó **el 5%** con Invoke-Obfuscation, añadiendo el sufijo `obf-out-{técnica}`.
- **Relación a verificar [PENDIENTE]:** las dos cifras **no son necesariamente contradictorias**. Una lectura posible es que el 25% sea el total ofuscado con ambas herramientas y el 5% la parte correspondiente a Invoke-Obfuscation, pero la relación exacta debe comprobarse con el listado de archivos y el código de los scripts de ofuscación.
- **No se asume que todos los archivos ofuscados puedan emparejarse automáticamente con su original.** Si algunos nombres conservan el hash del original, por ejemplo `{sha256_original}.obf-out-{técnica}.ps1`, podrían reconstruirse pares para ese subconjunto. **[PENDIENTE]** verificarlo con el **listado de nombres** de `malicious_samples/` (solo metadatos, sin abrir archivos).
- Las variantes con Chameleon no tienen sufijo documentado, así que su emparejamiento es **[PENDIENTE]** y podría no ser posible.
- Aunque existan pares, la equivalencia funcional de cada variante tendría que revisarse según [dataset_selection_plan.md](dataset_selection_plan.md#3-equivalencia-funcional-entre-original-y-variantes).

### Licencia
- **[COMPROBADO]** El repositorio **no muestra archivo de licencia** en su raíz ni en la ficha del proyecto. Sin licencia explícita, no hay concesión de derechos de redistribución.
- Las muestras provienen de terceros con licencias diversas (por ejemplo, PowerSploit y atomic-red-team tienen sus propias licencias) o de sandboxes con sus propios términos.
- **Consecuencia:** se puede consultar para investigación local, pero **no se redistribuyen muestras**. Cuando se use un script de un proyecto ofensivo conocido, tomarlo **del repositorio original** para tener procedencia y licencia claras.

### Duplicados
- **[AUTOR]** El nombrado por SHA-256 elimina **duplicados exactos**, pero no casi-duplicados.
- Al incluir MPSD y varios repos que reutilizan módulos (Empire y PowerSploit comparten código histórico), es muy probable que existan casi-duplicados. **[PENDIENTE]** medirlo con similitud de tokens en entorno aislado.

### Riesgos
- Contiene **malware real** de sandboxes. Clonar el repositorio en Windows hará que el antivirus ponga archivos en cuarentena. Según [security.md](security.md), **no desactivaremos protecciones**, así que cualquier inspección de contenido debe hacerse en un entorno aislado y autorizado (Fase 0B).
- Muchos scripts de frameworks como Empire o PowerSploit tienen **cientos o miles de líneas**, lo que choca con la ventana de contexto del LLM.
- Sesgo hacia frameworks ofensivos públicos muy conocidos: el LLM puede **reconocerlos por el nombre** (memorización) y no por el comportamiento.

### Utilidad para el experimento
- **Limitada como fuente principal de evaluación.** Útil para:
  1. Consultar los **metadatos** (JSON de Triage y Hybrid Analysis) y entender familias y técnicas reales.
  2. Seleccionar, en la Fase 0B y en entorno aislado, **un pequeño subconjunto** (≤ 6 originales) de scripts cortos con comportamiento verificable manualmente, preferiblemente tomados del repositorio original.

---

## Fuente C — Invoke-Obfuscation

**URL:** https://github.com/danielbohannon/Invoke-Obfuscation

### Qué ofrece
- **[COMPROBADO]** Es una **herramienta de generación de transformaciones, no un dataset etiquetado**: un ofuscador de comandos y scripts PowerShell (v2.0+), versión 1.8 con actualizaciones 1.8.1 (COMPRESS) y 1.8.2 (AST).
- **[COMPROBADO]** Propósito declarado por el autor: ayudar al Blue Team a simular comandos ofuscados para probar sus capacidades de detección.
- **[COMPROBADO]** Familias de técnicas, cada una en su propio script `Out-*.ps1`:
  - **TOKEN**: ofuscación por token (comillas, backticks, mayúsculas aleatorias, reordenamiento con operador `-f`, tipos).
  - **STRING**: concatenación, reordenamiento, inversión.
  - **ENCODING**: ASCII, hexadecimal, octal, binario, SecureString, BXOR, solo caracteres especiales, espacios en blanco.
  - **COMPRESS**: compresión a una sola línea.
  - **AST**: manipulación del árbol sintáctico.
  - **LAUNCHER**: formas de lanzar `powershell.exe` (stdin, clip, WMIC, RUNDLL, MSHTA, etc.).
- **[COMPROBADO]** Desde la v1.6 tiene **modo CLI** automatizable, por ejemplo: `Invoke-Obfuscation -ScriptBlock {...} -Command 'Token\All\1,Encoding\1' -Quiet`.
- **[COMPROBADO]** Desde la v1.6, las funciones STRING, ENCODING y LAUNCHER añaden **envoltorios `Invoke-Expression`/IEX** con muchas sintaxis alternativas.

### Licencia
- **[COMPROBADO]** **Apache 2.0.**

### Relevancia metodológica
- **Hallazgo clave:** la mayoría de técnicas de Invoke-Obfuscation (operador `-f`, `[char]`, ASCII/hex/octal/binario, BXOR, SecureString, compresión, AST) dependen de evaluación en tiempo de ejecución y **quedan fuera del alcance previsto del desofuscador** (Base64/`-EncodedCommand`, concatenación de literales, sustitución de variables literales).
  - Si todo el conjunto se generara con esta herramienta, la configuración C apenas diferiría de B **por diseño**, no por el modelo.
  - **Por eso conviene usarla para el estrato de técnicas no soportadas** y generar las variantes soportadas con un generador propio, con las mitigaciones de sesgo de [dataset_selection_plan.md](dataset_selection_plan.md#43-generador-propio-y-mitigación-de-sesgo).
- **Hallazgo clave para la taxonomía:** como la herramienta añade envoltorios IEX, **una variante ofuscada puede contener ejecución dinámica que el original no tenía**. La taxonomía aprobada no asigna B02 por esos envoltorios; se registran en `added_operations` y afectan al estado de equivalencia de la variante.

### Riesgos
- Es una herramienta PowerShell externa: ejecutarla implica correr código de terceros. **No se ejecutó.** Su uso queda **[PENDIENTE]** para la Fase 0B, en un entorno aislado (VM o contenedor con `pwsh`), aplicada solo a scripts propios inertes.
- **[PENDIENTE]** Verificar en el código si existen comandos interactivos que **ejecuten** el resultado ofuscado. De existir, no deben usarse. En modo CLI se usará solo la generación de texto.

### Utilidad para el experimento
- **Alta, como generador controlado** de variantes no soportadas, con registro exacto del comando usado (`transform_params`), lo que hace las variantes **reproducibles**.

---

## Fuente adicional evaluada — MPSD (das-lab)

**URL:** https://github.com/das-lab/mpsd
**Paper:** Fang Yong, Zhou Xiangyu, Huang Cheng. *Effective method for detecting malicious PowerShell scripts based on hybrid features*. Neurocomputing, 2021, 448: 30–39.

- **[COMPROBADO]** Tres carpetas:
  - `malicious_pure/`: muestras maliciosas.
  - `powershell_benign_dataset/`: muestras benignas.
  - `mixed_malicious/`: cada muestra combina un script malicioso con uno benigno aleatorio.
- **[COMPROBADO]** Los archivos de `malicious_pure/` se nombran con números secuenciales (`1.ps1`, `10.ps1`, ...) y están **en texto plano en GitHub**. Los fragmentos visibles en los resultados de búsqueda muestran cargadores de shellcode y payloads codificados, es decir, **contenido malicioso real**.
- **[COMPROBADO]** No se observó archivo de licencia en la información revisada. **[PENDIENTE]** confirmarlo.
- **[AUTOR, fuente secundaria]** Un trabajo posterior (AutoMalDesc, arXiv 2511.13333) describe este dataset con unas 4.200 muestras maliciosas y un número comparable de benignas. **[PENDIENTE]** contarlas directamente.
- **Etiquetas:** las etiquetas binarias (malicioso/benigno) son **declaradas por los autores** y **no equivalen a etiquetas de comportamiento B01–B07 verificadas**. Tampoco se han verificado de forma independiente.
- **Limitaciones:** sin pares original/ofuscado y con riesgo de casi-duplicados (Fa2y lo incluye). La carpeta `mixed_malicious/` mezcla código de dos procedencias, lo que complica asignar evidencia.
- **Utilidad:** referencia académica y posible fuente de benignos. Usarla solo con revisión manual y en entorno aislado.

---

## Fuente adicional — Azure-Samples/azure-docs-powershell-samples

**URL:** https://github.com/Azure-Samples/azure-docs-powershell-samples
**Revisión:** documental, 2026-10-29 (página del repositorio y `LICENSE.md`). No se descargó ningún script.

### Qué ofrece
- **[COMPROBADO]** Descripción del repositorio: scripts de ejemplo de Azure PowerShell usados en la documentación oficial de Microsoft (learn.microsoft.com).
- **[COMPROBADO]** El README los presenta como **ejemplos no destinados a producción**, para aprendizaje y experimentación.
- **[COMPROBADO]** Rama por defecto `main`. Carpetas de primer nivel en la fecha de revisión: `azure-cosmosdb`, `azure-migrate`, `azure-portal`, `azure-sql`, `container-registry`, `expressroute-gateway`, `expressroute`, `hdinsight`, `managed-disks`, `migration-assistant`, `storage`, `virtual-network-manager` (más `.github`).
- **[COMPROBADO]** Normas de contribución del README: los ejemplos son solo para documentación, deben usar únicamente comandos del módulo Az, no se aceptan módulos (`.psm1`), binarios, imágenes ni archivos comprimidos, y se exige un acuerdo de licencia de contribución (CLA).
- **[PENDIENTE]** Número de scripts, tamaño y fecha de la última actualización.

### Licencia
- **[COMPROBADO]** **MIT**, con la línea `Copyright (c) Microsoft Corporation.` en `LICENSE.md`.
- La licencia MIT permite adaptar y redistribuir conservando el aviso de copyright y la licencia. Si se adapta un script, se registra en el manifiesto con `source_license = MIT` y la atribución en `provenance_notes`.

### Riesgos y limitaciones
- Los scripts son de **administración de nube** (módulo Az): crean o modifican recursos de Azure. Representan bien el estilo de un script administrativo legítimo, pero sus comportamientos se corresponden poco con B01–B07, que están orientados al host.
- **[PENDIENTE]** Decidir si las llamadas a cmdlets de gestión de Azure cuentan como B06 o se tratan como operación administrativa sin etiqueta (ver [behavior_taxonomy.md](behavior_taxonomy.md)).
- Al ser ejemplos de documentación pública, es probable que formen parte de los datos de entrenamiento del LLM.
- Algunos scripts podrían superar el tope de tamaño propuesto (≤ 150 líneas).
- Como cualquier script, se analizan solo de forma estática; **nunca se ejecutan** (requerirían además una suscripción de Azure).

### Utilidad para el experimento
- **Moderada, como fuente de S1** (administrativos legítimos con licencia clara), sobre todo para medir falsos positivos de riesgo. Requiere seleccionar scripts cortos y, probablemente, complementarlos con administrativos orientados al host escritos por el equipo.

---

## Fuente adicional pendiente — dessertlab/offensive-powershell (Hugging Face)

- **[COMPROBADO]** Dataset en Hugging Face con licencia **GPL-3.0**, en formato parquet y dividido en `train`, `dev` y `test`. Es pequeño (decenas de kB por partición).
- **[PENDIENTE]** Revisar su ficha y contenido. Si incluye descripciones en lenguaje natural asociadas a cada fragmento, podría servir como apoyo para etiquetar comportamientos o para ejemplos de desarrollo. **No se incorpora hasta verificarlo**, y la GPL-3.0 impone condiciones a la redistribución que deben revisarse.

---

## Resumen y recomendación

| Fuente | Tipo | Licencia | Etiquetas útiles | Pares original/ofuscado | Uso recomendado |
|---|---|---|---|---|---|
| A. Revoke-Obfuscation | Framework + etiquetas de ofuscación + corpus externo | Apache 2.0 (código); corpus sin licencia declarada | Ofuscado / no ofuscado (no maliciosidad ni comportamiento) | No documentados | Referencia metodológica; fuente opcional de benignos tras revisión |
| B. Fa2y | Muestras maliciosas declaradas + scripts de recolección | Sin licencia visible | Implícita por procedencia, con ruido | Posibles para un subconjunto vía sufijo `obf-out-*` [PENDIENTE] | Metadatos; subconjunto pequeño en entorno aislado |
| C. Invoke-Obfuscation | Herramienta de transformación | Apache 2.0 | No aplica | Sí, si generamos nosotros | **Generador del estrato no soportado** |
| MPSD | Muestras maliciosas, benignas y mixtas | Sin licencia visible [PENDIENTE] | Binarias, declaradas por los autores | No | Referencia; benignos opcionales |
| Azure-Samples | Ejemplos administrativos de Azure | MIT | No aplica | No | Candidata para S1, con adaptación |

**Recomendación general:** ninguna fuente pública trae lo que el experimento necesita (pares original/ofuscado con etiquetas de comportamiento verificadas y equivalencia revisada). Por eso el ground truth debe **construirse**:

1. Originales propios (administrativos y simulaciones adversarias inertes) con comportamientos conocidos **por diseño**.
2. Variantes soportadas con un generador propio y determinista, con conjuntos sintácticos reservados.
3. Variantes no soportadas con Invoke-Obfuscation en modo CLI, dentro de un entorno aislado.
4. Un subconjunto pequeño y opcional de scripts públicos reales, revisados manualmente, para la evaluación de generalización.

El detalle está en [dataset_selection_plan.md](dataset_selection_plan.md).

## Referencias

- Revoke-Obfuscation: https://github.com/danielbohannon/Revoke-Obfuscation
- Revoke-Obfuscation DataScience: https://github.com/danielbohannon/Revoke-Obfuscation/blob/master/DataScience/README.md
- White paper Revoke-Obfuscation (Black Hat USA 2017): https://blackhat.com/docs/us-17/thursday/us-17-Bohannon-Revoke-Obfuscation-PowerShell-Obfuscation-Detection-And%20Evasion-Using-Science-wp.pdf
- PowerShellCorpus: http://aka.ms/PowerShellCorpus
- Malicious-PowerShell-Dataset: https://github.com/Fa2y/Malicious-PowerShell-Dataset
- Invoke-Obfuscation: https://github.com/danielbohannon/Invoke-Obfuscation
- MPSD: https://github.com/das-lab/mpsd
- AutoMalDesc (descripción secundaria de datasets PowerShell): https://arxiv.org/pdf/2511.13333
- dessertlab/offensive-powershell: https://huggingface.co/datasets/dessertlab/offensive-powershell
- Azure-Samples/azure-docs-powershell-samples: https://github.com/Azure-Samples/azure-docs-powershell-samples
