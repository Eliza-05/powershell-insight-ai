# Metodología de investigación

> Diseño experimental previsto. No se han ejecutado experimentos ni existen métricas.

## 1. Pregunta e hipótesis

**Pregunta:** ¿En qué medida la desofuscación estática previa mejora la capacidad de un LLM local para identificar y explicar comportamientos potencialmente maliciosos en scripts PowerShell ofuscados?

- **H1:** la desofuscación estática previa mejora el F1 en la identificación de comportamientos frente al análisis directo del LLM (C > B).
- **H2:** la desofuscación estática previa reduce las afirmaciones no respaldadas por evidencia (C < B).

Las hipótesis se aceptarán o rechazarán según los resultados; un resultado negativo es igualmente válido y se reportará.

## 2. Configuraciones experimentales

| ID | Nombre | Entrada | Procesamiento |
|---|---|---|---|
| **A** | Reglas sin LLM | Script ofuscado | Desofuscación estática + detección determinista |
| **B** | LLM directo | Script ofuscado | El LLM analiza el script sin preprocesamiento |
| **C** | Desofuscación + LLM | Script ofuscado + artefactos recuperados | El LLM recibe el script original y lo recuperado por el motor estático |

A actúa como línea base determinista. B y C usan el mismo modelo, la misma versión, los mismos parámetros de inferencia y la misma estructura de salida; solo cambia la entrada. Así, la diferencia B vs. C aísla el efecto de la desofuscación.

## 3. Evaluaciones

### 3.1 Identificación de comportamientos (A / B / C)
Clasificación multietiqueta: para cada script, qué comportamientos funcionales de la [taxonomía](behavior_taxonomy.md) (B01–B07) están presentes. Se compara la salida de cada configuración con las etiquetas de referencia. **Es la evaluación principal del proyecto.** Las técnicas de ofuscación y los envoltorios de ejecución añadidos por la ofuscación se reportan en campos propios y no cuentan como comportamientos.

### 3.2 Calidad explicativa (B / C)
Para cada afirmación del LLM se verifica:
- si la evidencia citada existe en el script o en los artefactos recuperados;
- si la interpretación es semánticamente correcta (revisión manual con rúbrica);
- si hay afirmaciones sin respaldo.

### 3.3 Recuperación de código (motor de desofuscación)
Con pares conocidos (script original ↔ versión ofuscada generada de forma controlada), se mide cuánto del contenido original recupera el motor estático, usando las cadenas clave esperadas (`expected_recovered_strings`) registradas en el manifiesto. Esta evaluación es independiente de la del LLM: que el modelo interprete una técnica que el motor no reconstruye no se penaliza en ninguna de las dos.

### 3.4 Valoración de riesgo (análisis secundario)
Además de los comportamientos, cada muestra tiene un tipo de escenario (`scenario_type`) y una valoración de riesgo sustentada (`risk_label`: `benign`, `suspicious`, `high_risk`, `unknown`). Este eje se analiza de forma secundaria, sobre todo para comprobar que la ofuscación no eleva por sí sola la valoración. Las simulaciones adversarias son escenarios de laboratorio y no se tratan como malware verificado. Ver [dataset_selection_plan.md](dataset_selection_plan.md#7-manifiesto-campos).

### 3.5 Evaluación controlada y de generalización
- **Controlada:** variantes cuyo comportamiento y transformación conocemos, generadas con las formas sintácticas usadas durante el desarrollo.
- **Generalización:** formas sintácticas reservadas que no se usaron durante el desarrollo, técnicas no soportadas (p. ej., Invoke-Obfuscation) y scripts públicos revisados.

Los resultados de cada grupo se reportan por separado y por tipo de transformación. Si se presenta un agregado, se explican las diferencias entre grupos. Detalle en [dataset_selection_plan.md](dataset_selection_plan.md#44-evaluación-controlada-y-de-generalización).

## 4. Criterios de evaluación previstos

| Criterio | Aplica a | Descripción |
|---|---|---|
| Precision | A, B, C | Comportamientos predichos que son correctos |
| Recall | A, B, C | Comportamientos reales que fueron detectados |
| F1 | A, B, C | Media armónica de precision y recall (micro y macro por comportamiento) |
| Validez de evidencias | B, C | Proporción de evidencias citadas que existen y respaldan la afirmación |
| Corrección semántica | B, C | Evaluación manual de la explicación según rúbrica |
| Afirmaciones no respaldadas | B, C | Número o proporción de afirmaciones sin evidencia verificable |
| Tiempo de procesamiento | A, B, C | Tiempo por script en hardware documentado |
| Estabilidad de respuestas | B, C | Concordancia entre ejecuciones repetidas sobre la misma entrada |
| Recuperación de código | Motor estático | Similitud entre contenido recuperado y original conocido |

La definición exacta de cada métrica (p. ej., medida de similitud, número de repeticiones, rúbrica semántica) se fijará antes de ejecutar la evaluación final y se registrará en `experiments/configurations/`.

## 5. Ground truth

- El ground truth se **construye** (originales propios con comportamiento conocido por diseño y variantes generadas de forma controlada), porque ninguna fuente pública ofrece pares original/ofuscado con etiquetas de comportamiento verificadas ([dataset_audit.md](dataset_audit.md)).
- Cada script del conjunto de evaluación tiene etiquetas de comportamiento asignadas **antes** de ejecutar las configuraciones, según los criterios de la taxonomía.
- Los metadatos de cada muestra (hash SHA-256, procedencia, licencia, familia, transformación, equivalencia) se registran en el manifiesto `datasets/metadata/manifest_template.csv`; las evidencias, en archivos JSON según `datasets/metadata/annotations_template.json`.
- Las etiquetas de un dataset público no se aceptan sin revisión: un repositorio etiquetado como "malicioso" no define qué comportamientos contiene cada script.
- **Revisión humana:** no se presupone que haya dos anotadores. Si solo una persona anota, se documenta como limitación. Si existe una segunda revisión independiente real, se registra y se reporta el acuerdo; el kappa de Cohen solo se calcula si hay suficientes casos doblemente anotados para interpretarlo. No se registran revisiones ni concordancias que no hayan ocurrido.

## 6. Equivalencia funcional entre original y variantes

Las etiquetas se asignan al original. Una variante solo hereda esas etiquetas cuando una revisión estática documentada no encontró diferencias funcionales (`reviewed_static`), y solo esas variantes entran en la comparación principal. Las variantes con equivalencia parcial (p. ej., con envoltorios `Invoke-Expression` añadidos por la ofuscación), no verificada o con comportamiento alterado se analizan por separado o se excluyen. La equivalencia completa no puede demostrarse en general mediante análisis estático; esta limitación se reporta. Detalle en [dataset_selection_plan.md](dataset_selection_plan.md#3-equivalencia-funcional-entre-original-y-variantes).

## 7. Separación de datos y prevención de contaminación

- **Unidad de independencia:** la familia o el script base, no la variante.
- **Conjuntos separados:** desarrollo (para construir reglas y ajustar prompts) y prueba (solo para la medición final), con una proporción inicial **cercana a 50/50 por familias**, ajustable para que cada comportamiento tenga positivos en ambos conjuntos. Meta inicial: 20–30 scripts base.
- **Piloto separado:** los casos del [piloto](pilot_plan.md) no se reutilizan en desarrollo ni en prueba.
- **Separación por familias:** las variantes de un mismo base y los bases de una misma familia quedan en el mismo conjunto. Se revisan casi-duplicados antes de congelar.
- **Sesgo del generador:** se reservan formas sintácticas que no se usan durante el desarrollo, se incluyen técnicas no soportadas y se reportan los resultados por transformación ([dataset_selection_plan.md](dataset_selection_plan.md#43-generador-propio-y-mitigación-de-sesgo)).
- **Congelación:** el conjunto de prueba, la taxonomía, las reglas, los prompts y la versión del modelo se congelan antes de los ajustes definitivos. Cualquier cambio posterior se documenta en este archivo con su motivo.
- **Contaminación del modelo:** los scripts públicos pueden formar parte de los datos de entrenamiento del LLM; esta limitación se documentará en el informe.

## 8. Reproducibilidad

- Registrar versión exacta del modelo (nombre, etiqueta y digest en Ollama), parámetros de inferencia y semilla.
- Versionar prompts en `experiments/prompts/` y configuraciones en `experiments/configurations/`.
- Registrar hardware y tiempos.
- Conservar identificadores y hashes de cada muestra.
- Guardar resultados por ejecución con referencia a la configuración utilizada.

## 9. Limitaciones previstas

- Tamaño del dataset limitado por el etiquetado manual. Con 20–30 familias, los resultados son **exploratorios** y no permiten conclusiones estadísticas generales; algunas categorías pueden tener pocos positivos.
- El análisis estático no puede resolver toda ofuscación dependiente de la ejecución.
- La equivalencia funcional entre original y variantes se revisa estáticamente, sin demostración formal.
- Si el etiquetado lo realiza una sola persona, no puede estimarse el acuerdo entre anotadores.
- La corrección semántica incluye juicio humano.
- Los resultados dependen del modelo elegido y no se generalizan automáticamente a otros LLM.
