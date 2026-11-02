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

**Niveles de soporte de la evidencia** (adoptados al cierre de la Fase 0B; ver la sección 10):

1. **Coincidencia literal:** la cita existe en una fuente identificable (script original, variante ofuscada o artefacto recuperado). Se comprueba de forma automática.
2. **Soporte individual:** el fragmento basta por sí solo para justificar el comportamiento.
3. **Soporte contextual:** varios fragmentos relacionados justifican juntos el hallazgo.
4. **Soporte insuficiente:** la evidencia existe, pero no sostiene la conclusión.
5. **Errores en las explicaciones textuales:** operaciones inexistentes, afirmaciones no establecidas, especulación o clasificación contraria a la taxonomía.

**Métrica principal: política estricta.** Solo cuentan los fragmentos que el sistema citó o recuperó y que se pueden verificar contra el script. Como evaluación **secundaria**, claramente separada, se informa la política permisiva, que admite contexto del script no citado. Una referencia decodificada preparada por el equipo nunca cuenta como recuperación del sistema. Los veredictos semánticos producidos con ayuda de IA son **preliminares** hasta su revisión humana.

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
| Validez de evidencias | B, C | Proporción de evidencias citadas que existen y respaldan la afirmación. Principal: hallazgos con soporte individual o contextual según la política estricta (sección 3.2); secundaria: política permisiva |
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
- **Congelación:** el conjunto de prueba, la taxonomía, las reglas, los prompts y la versión del modelo se congelan antes de los ajustes definitivos. Cualquier cambio posterior se documenta en este archivo con su motivo (sección 10).
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

## 10. Desviaciones y decisiones metodológicas registradas

Cada desviación respecto de un plan aprobado se registra aquí con su motivo, su alcance y sus condiciones. **Los criterios originales no se modifican retroactivamente.**

### DEV-01 — Inicio de la Fase 1A sin modelo seleccionado (decisión D1, 2026-11-01)

| Campo | Contenido |
|---|---|
| Regla original | [pilot_plan.md](pilot_plan.md) §6: si el modelo no cumple los criterios de viabilidad, "se prueba otro tamaño o modelo antes de la Fase 1" |
| Situación | Qwen2.5-Coder 7B no superó el criterio de etiquetas exactas en el piloto v1 (4/7 frente a ≥ 5/7) ([pilot_results.md](pilot_results.md)) |
| Desviación | La **Fase 1A** (desofuscador estático determinista) puede empezar sin haber seleccionado el LLM, una vez cerrada formalmente la Fase 0B |
| Justificación | La Fase 1A no usa el LLM: implementa la recuperación estática (configuración A) y sus pruebas |
| Alcance | Solo la Fase 1A. No autoriza a usar el LLM en la Fase 1A ni a ajustar prompts o modelos con P1–P8 |
| Condiciones | (1) Qwen2.5-Coder 7B queda solo como **candidato provisional / línea base experimental**, no como modelo del proyecto. (2) La **selección definitiva del LLM es obligatoria antes de la Fase 2 y antes de cualquier experimento comparativo definitivo A/B/C**. (3) Esa selección se hará con **ejemplos nuevos** registrados antes de ejecutar; P1–P8 no bastan por sí solos para seleccionar ni ajustar el modelo. (4) Los criterios del §6 del plan del piloto se mantienen sin cambios |
| Aprobación | Propietario del proyecto, 2026-11-01 |
| Registro | [phase0b_closure.md](phase0b_closure.md) §12, [roadmap.md](roadmap.md) |

### DEV-02 — Traslado de actividades de la Fase 0B (decisión D3, 2026-11-01)

Las actividades de la Fase 0B que no se completaron se trasladan a la Fase 1A, la Fase 1B, la Fase 4 y a un prerrequisito previo al uso de muestras externas. Las fases de destino, las dependencias y los criterios de aceptación están en [roadmap.md](roadmap.md). **Mientras no exista el entorno aislado, el proyecto solo usa scripts propios y controlados.** Aprobación: propietario del proyecto, 2026-11-01.

### DEC-01 — Política estricta de evidencias como métrica principal (2026-11-01)

Ver la sección 3.2. La política permisiva se conserva como evaluación secundaria. No se modifican los resultados ni las respuestas originales del piloto v1. Aprobación: propietario del proyecto, 2026-11-01.
- La corrección semántica incluye juicio humano.
- Los resultados dependen del modelo elegido y no se generalizan automáticamente a otros LLM.
