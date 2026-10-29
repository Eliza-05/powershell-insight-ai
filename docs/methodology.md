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
Clasificación multietiqueta: para cada script, qué comportamientos de la [taxonomía](behavior_taxonomy.md) están presentes. Se compara la salida de cada configuración con las etiquetas de referencia.

### 3.2 Calidad explicativa (B / C)
Para cada afirmación del LLM se verifica:
- si la evidencia citada existe en el script o en los artefactos recuperados;
- si la interpretación es semánticamente correcta (revisión manual con rúbrica);
- si hay afirmaciones sin respaldo.

### 3.3 Recuperación de código (motor de desofuscación)
Con pares conocidos (script original ↔ versión ofuscada generada de forma controlada), se mide cuánto del contenido original recupera el motor estático.

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

- Cada script del conjunto de evaluación debe tener etiquetas de comportamiento asignadas **antes** de ejecutar las configuraciones, según los criterios de la taxonomía.
- Las etiquetas se documentan en `datasets/metadata/` junto con el hash SHA-256 del script, su procedencia y quién/cómo se etiquetó.
- Las etiquetas de un dataset público no se aceptan sin revisión: un repositorio etiquetado como "malicioso" no define qué comportamientos contiene cada script.
- Cuando sea posible, una muestra del etiquetado se revisará de forma independiente para estimar su consistencia.

## 6. Separación de datos y prevención de contaminación

- **Conjuntos separados:** desarrollo (para construir reglas y ajustar prompts) y evaluación (solo para la medición final).
- **Separación por familias:** variantes de un mismo script base (p. ej., distintas ofuscaciones del mismo código) deben quedar en el mismo conjunto, para no evaluar con variantes de scripts vistos durante el desarrollo.
- **Congelación:** el conjunto de evaluación, la taxonomía, las reglas, los prompts y la versión del modelo se congelan antes de la evaluación final. No se modifican después para mejorar resultados.
- **Contaminación del modelo:** los scripts públicos pueden formar parte de los datos de entrenamiento del LLM; esta limitación se documentará en el informe.

## 7. Reproducibilidad

- Registrar versión exacta del modelo (nombre, etiqueta y digest en Ollama), parámetros de inferencia y semilla.
- Versionar prompts en `experiments/prompts/` y configuraciones en `experiments/configurations/`.
- Registrar hardware y tiempos.
- Conservar identificadores y hashes de cada muestra.
- Guardar resultados por ejecución con referencia a la configuración utilizada.

## 8. Limitaciones previstas

- Tamaño del dataset limitado por el etiquetado manual.
- El análisis estático no puede resolver toda ofuscación dependiente de la ejecución.
- La corrección semántica incluye juicio humano.
- Los resultados dependen del modelo elegido y no se generalizan automáticamente a otros LLM.
