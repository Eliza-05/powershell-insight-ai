# Hoja de ruta

> No se fijan fechas. El cronograma debe ajustarse a las fechas oficiales del curso. La inicialización del repositorio (estructura y documentación) es el punto de partida y precede a la Fase 0.

```mermaid
flowchart LR
    F0[Fase 0<br/>Datasets y modelo] --> F1[Fase 1<br/>Motor estático y reglas]
    F1 --> F2[Fase 2<br/>Integración LLM]
    F1 -. contratos .-> F3[Fase 3<br/>Frontend e integración]
    F2 --> F3
    F2 --> F4[Fase 4<br/>Experimentos y métricas]
    F3 --> F5[Fase 5<br/>Informe y demostración]
    F4 --> F5
```

## Fase 0 — Validación de datasets y modelo

- **Objetivo:** confirmar que los datos y el modelo candidatos son viables.
- **Dependencias:** ninguna.

### Fase 0A — Investigación documental y diseño (documentación preparada, pendiente de aprobación)

- **Actividades:** auditoría documental de las fuentes; diseño del dataset, del manifiesto y de las anotaciones; revisión de la taxonomía; diseño del piloto.
- **Entregables:** [dataset_audit.md](dataset_audit.md), [dataset_selection_plan.md](dataset_selection_plan.md), [pilot_plan.md](pilot_plan.md), taxonomía [v0.2 (B01–B07)](behavior_taxonomy.md), plantillas `datasets/metadata/manifest_template.csv` y `datasets/metadata/annotations_template.json`.
- **Criterios de aceptación:** el equipo aprueba el diseño y resuelve las decisiones pendientes listadas en el plan de selección.

### Fase 0B — Piloto del modelo y verificación de fuentes

- **Actividades:**
  - Definir el entorno aislado e inspeccionar en él las fuentes seleccionadas (contenido, duplicados, licencias pendientes).
  - Escribir los casos del piloto, con sus referencias en el manifiesto y en las anotaciones.
  - Instalar Ollama y correr el piloto con Qwen2.5-Coder 7B: JSON válido, comportamientos, evidencias, incertidumbre, prompt injection, estabilidad y latencia.
  - Comenzar a escribir y etiquetar los scripts base y asignar familias a desarrollo y prueba.
- **Entregables:** resultados del piloto con salidas crudas, decisión de modelo (tag y digest), prompt y esquema JSON versionados, primeras filas reales del manifiesto.
- **Criterios de aceptación:** el modelo cumple los criterios de viabilidad de [pilot_plan.md](pilot_plan.md#6-criterios-de-viabilidad-del-modelo) o se documenta el cambio de candidato; la partición por familias está documentada.

## Fase 1 — Motor estático y reglas

- **Objetivo:** implementar la configuración A.
- **Actividades:** esqueleto del backend; esquemas Pydantic; transformaciones de desofuscación con trazabilidad; reglas B01–B07; generador determinista de variantes; pruebas Pytest con muestras inertes.
- **Entregables:** servicios `deobfuscation` y `detection`, esquemas, suite de pruebas.
- **Criterios de aceptación:** pruebas pasan; ningún componente ejecuta código del script; límites de tamaño y profundidad aplicados.
- **Dependencias:** Fase 0 (taxonomía aprobada y criterios validados con el conjunto de desarrollo).

## Fase 2 — Integración del LLM

- **Objetivo:** implementar las configuraciones B y C y la validación de evidencias.
- **Actividades:** cliente Ollama; plantillas de prompt versionadas; parseo de salida estructurada; validador de evidencias; mitigaciones de prompt injection.
- **Entregables:** servicios `llm` y `evidence`, prompts en `experiments/prompts/`.
- **Criterios de aceptación:** B y C generan salidas válidas según el esquema; las afirmaciones no respaldadas se detectan; modelo y parámetros quedan registrados.
- **Dependencias:** Fase 1.

## Fase 3 — Frontend e integración

- **Objetivo:** interfaz web para analizar y visualizar resultados.
- **Actividades:** proyecto Vite + React + TypeScript + Tailwind; editor de código; vistas de hallazgos y evidencias; endpoints FastAPI; integración extremo a extremo.
- **Entregables:** aplicación web funcional en local.
- **Criterios de aceptación:** un script de ejemplo inerte puede analizarse de punta a punta; ninguna lógica de análisis ni credencial reside en el navegador.
- **Dependencias:** contratos de la Fase 1 (puede avanzar en paralelo una vez definidos); Fase 2 para la integración completa.

## Fase 4 — Experimentos y métricas

- **Objetivo:** evaluar H1 y H2.
- **Actividades:** congelar dataset, prompts y modelo; ejecutar A/B/C; calcular métricas; revisión semántica manual; repeticiones para estabilidad.
- **Entregables:** resultados en `experiments/results/`, scripts de evaluación, tablas y figuras.
- **Criterios de aceptación:** resultados reproducibles a partir de la configuración registrada; el conjunto de evaluación no se modificó tras la congelación.
- **Dependencias:** Fases 0, 1 y 2.

## Fase 5 — Informe y demostración

- **Objetivo:** comunicar resultados.
- **Actividades:** redacción del informe (metodología, resultados, limitaciones); preparación de la demostración con muestras inertes; actualización del README.
- **Entregables:** informe final, presentación, demostración.
- **Criterios de aceptación:** las conclusiones se sustentan en los resultados obtenidos, incluidos los negativos.
- **Dependencias:** Fases 3 y 4.
