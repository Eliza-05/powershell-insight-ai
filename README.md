# PowerShell Insight AI

LLM-powered static analysis and deobfuscation of PowerShell scripts for cybersecurity research.

**Título académico:** Sistema inteligente de análisis estático, desofuscación y caracterización de scripts PowerShell mediante un modelo de lenguaje local.

Proyecto final de la asignatura **Ciberinteligencia**.

> **Estado: Fase 2 implementada con Qwen3.5 provisional bajo autorización prospectiva DEV-03.** [Integración A/B/C, uso y límites](docs/phase2_integration.md); [cierre técnico y pruebas reales, incluidos rechazos](docs/phase2_closure.md). El piloto v2 sigue **PENDIENTE / INCONCLUSO**: 58 intentos, 68 llamadas de selección pendientes; hashes, criterios e incidente de memoria conservados. Qwen3.5 no está validado científicamente. [Acta histórica](docs/phase_model_selection_closure.md). FastAPI/React y evaluación final no iniciados.

---

## 1. Descripción general

PowerShell Insight AI será una aplicación web para analizar de forma **estática** scripts PowerShell potencialmente maliciosos u ofuscados. El sistema intentará recuperar fragmentos de código ocultos mediante transformaciones controladas, identificar comportamientos con un motor de reglas determinista y apoyarse en un modelo de lenguaje ejecutado localmente (Ollama) para explicar esos comportamientos, validando cada afirmación contra evidencias concretas del script.

## 2. Problema que aborda

PowerShell es una herramienta legítima de administración presente en Windows, pero también es ampliamente utilizada en ataques (descarga y ejecución de cargas, persistencia, evasión de defensas). Los atacantes suelen ofuscar estos scripts (codificación Base64, concatenación, reordenamiento de cadenas, invocación dinámica) para dificultar su lectura y evadir firmas. El análisis manual es lento y requiere experiencia; los LLM prometen acelerar la interpretación, pero pueden fallar ante la ofuscación o producir afirmaciones sin respaldo.

## 3. Objetivo principal

Desarrollar y evaluar un prototipo que combine desofuscación estática, reglas deterministas y un LLM local para caracterizar scripts PowerShell, y medir experimentalmente si la desofuscación previa mejora la identificación y explicación de comportamientos.

**Pregunta de investigación:** ¿En qué medida la desofuscación estática previa mejora la capacidad de un LLM local para identificar y explicar comportamientos potencialmente maliciosos en scripts PowerShell ofuscados?

**Hipótesis (pendientes de evaluación, no comprobadas):**

- **H1:** la desofuscación estática previa mejora el F1 en la identificación de comportamientos frente al análisis directo del LLM.
- **H2:** la desofuscación estática previa reduce las afirmaciones no respaldadas por evidencia.

## 4. Capacidades previstas

- Carga y visualización de scripts PowerShell en un editor web.
- Desofuscación estática (sin ejecutar el script) de técnicas comunes.
- Identificación determinista de siete comportamientos funcionales (B01–B07) según una [taxonomía propia](docs/behavior_taxonomy.md), separada del registro de técnicas de ofuscación y de la valoración de riesgo.
- Explicación asistida por un LLM local, con salida estructurada.
- Validación y trazabilidad de evidencias (cada hallazgo vinculado a fragmentos del script).
- Mapeo opcional a técnicas de MITRE ATT&CK.
- Módulo de evaluación experimental para comparar configuraciones.

## 5. Stack tecnológico

| Componente | Tecnología |
|---|---|
| Piloto v2 del LLM | Dataset 24+24 aprobado globalmente y congelado; 6 tecnicas +24 desarrollo +24 revision +4 seleccion. Parada por compromiso <2 GiB; 68 pendientes, sin validacion. [Acta](docs/phase_model_selection_closure.md) |
| Frontend | React + TypeScript + Vite |
| Estilos | Tailwind CSS |
| Editor de código | Monaco Editor (candidato) |
| Backend | Python + FastAPI |
| LLM | Ollama (local) |
| Modelo del piloto v2 | Qwen3.5 4B Q4_K_M: pendiente/inconcluso, no validado; v1 permanece historico |
| Validación estructurada | Pydantic |
| Análisis experimental | Pandas + scikit-learn |
| Pruebas de backend | Pytest |
| MITRE ATT&CK | STIX 2.1 (opcional) |

El piloto v2 reutiliza el entorno existente de Ollama, Pydantic y Pytest, con transporte HTTP y contadores Windows de la biblioteca estandar; no instala dependencias nuevas. Los requisitos del piloto historico se conservan en [backend/requirements-pilot.txt](backend/requirements-pilot.txt).

Para preparar el entorno local (`.venv`, Ollama, modelo, pruebas y piloto) en Windows, ver [docs/setup_windows.md](docs/setup_windows.md).

## 6. Arquitectura general

```text
CLI / futura API ──► AnalysisService ──► A: desofuscador 1A + detector 1B
                                    ├─► B: original ──► Ollama ──► validación
                                    └─► C: original + evidencia 1A ──► Ollama ──► validación
```

Detalle completo en [docs/architecture.md](docs/architecture.md).

## 7. Estructura del repositorio

```text
powershell-insight-ai/
├── frontend/src/            # Aplicación React (components, pages, services, hooks, types, utils)
├── backend/
│   ├── app/
│   │   ├── api/             # Endpoints REST
│   │   ├── core/            # Configuración y utilidades compartidas
│   │   ├── schemas/         # Contratos Pydantic
│   │   └── services/
│   │       ├── deobfuscation/        # Motor de desofuscación estática
│   │       ├── behavior_detection/   # Motor determinista de comportamientos
│   │       ├── pipelines/            # Aplicación A/B/C y adaptador Ollama
│   │       ├── llm/                  # Servicios históricos de los pilotos
│   │       ├── evidence/             # Validación de evidencias
│   │       └── threat_intelligence/  # MITRE ATT&CK (opcional)
│   └── tests/               # Pruebas Pytest
├── datasets/
│   ├── safe_samples/        # Muestras benignas o inertes revisadas
│   └── metadata/            # Inventarios, etiquetas, hashes y procedencia
├── experiments/
│   ├── prompts/             # Plantillas de prompts versionadas
│   ├── evaluation/          # Scripts de métricas
│   ├── configurations/      # Configuraciones A/B/C
│   └── results/             # Resultados pequeños y revisados
├── docs/                    # Documentación técnica y metodológica
├── .env.example
└── .gitignore
```

## 8. Metodología experimental (resumen)

Se compararán tres configuraciones sobre un conjunto de scripts etiquetado:

- **A — Reglas sin LLM:** desofuscación y detección deterministas.
- **B — LLM directo:** el modelo analiza el script ofuscado sin preprocesamiento.
- **C — Desofuscación + LLM:** el modelo recibe el script original y los elementos recuperados por el motor estático.

Se evaluarán la identificación de comportamientos (precision, recall, F1; evaluación principal), la calidad explicativa (validez de evidencias, afirmaciones no respaldadas) y la recuperación de código. El ground truth se construye con 20–30 scripts base propios (administrativos y simulaciones inertes) y variantes generadas de forma controlada, divididos por familias entre desarrollo y prueba. Los resultados de la evaluación controlada y de generalización se reportan por separado y, dado el tamaño del conjunto, se consideran exploratorios. Detalle en [docs/methodology.md](docs/methodology.md) y [docs/dataset_selection_plan.md](docs/dataset_selection_plan.md).

## 9. Estado actual

| Elemento | Estado |
|---|---|
| Estructura del repositorio | ✅ Creada |
| Documentación inicial | ✅ Creada |
| Fase 0A: auditoría documental de fuentes y diseño del dataset y del piloto | 📝 Documentación preparada, pendiente de aprobación |
| Fase 0B: verificación de fuentes en entorno aislado | ↪️ Trasladada: prerrequisito antes de usar muestras externas (decisión D3, [roadmap](docs/roadmap.md)) |
| Fase 0B: piloto del modelo en Ollama | ✅ Cerrada formalmente (2026-11-01); D2 aprobada con observaciones para las 20 anotaciones y la v0.2 completa. Qwen2.5-Coder 7B queda histórico, sin nuevas ejecuciones. Se mantienen DEV-02 y DEC-01 ([resultados](docs/pilot_results.md), [cierre](docs/phase0b_closure.md)); DEV-03 permite desarrollo de Fase 2 con Qwen3.5 provisional sin aprobar calidad |
| Fase 1A: desofuscación estática | Aprobada, cerrada y publicada por el responsable en el [subconjunto documentado](docs/deobfuscator.md); 274 pruebas de referencia preservadas. [Acta y limitación residual de reproducibilidad binaria](docs/phase1a_closure.md) |
| Fase 1B: detección determinista | Aprobada técnicamente y cerrada formalmente por el responsable: 12 reglas y siete categorías parciales; 488 pruebas aprobadas. FN P3/P7 aceptados. [Cierre formal](docs/phase1b_closure.md); [contrato y resultados](docs/behavior_detector.md). Publicación, dataset final y generador pendientes |
| Dataset definitivo A/B/C | ⏳ No iniciado (solo plantillas) |
| Motor de desofuscación | Implementado en el subconjunto de la Fase 1A: Base64, concatenación y variables; `-f` detectado sin resolución. [Contrato y límites](docs/deobfuscator.md) |
| Motor de reglas | Aprobado en el [subconjunto documentado de B01–B07](docs/behavior_detector.md), sin riesgo ni LLM; no implica evaluación independiente definitiva |
| Integración LLM | Implementada con Qwen3.5 provisional y servicios A/B/C. [Contratos, seguridad y limitaciones](docs/phase2_integration.md); [pruebas y estado de entrega](docs/phase2_closure.md). No implica aprobación científica |
| Frontend | ⏳ No iniciado |
| Experimento definitivo A/B/C | No iniciado; los pilotos de modelos son independientes de esa evaluacion |

## 10. Próximas fases

Ver [docs/roadmap.md](docs/roadmap.md). La integración permite preparar la Fase 3; la validación pendiente del modelo y la evaluación independiente siguen siendo obligaciones separadas. No se inicia la Fase 3 en esta entrega.

## 11. Precauciones de seguridad

- El sistema realiza **exclusivamente análisis estático**: nunca ejecuta ni evalúa scripts.
- El repositorio **no contiene malware real**. Las muestras externas solo podrán manejarse fuera del repositorio, en un entorno aislado, y los directorios correspondientes están excluidos por `.gitignore`. Ese entorno **aún no existe**; mientras tanto, el proyecto solo usa scripts propios y controlados.
- El contenido de los scripts (comentarios, cadenas) se trata como entrada no confiable, incluida la prevención de *prompt injection* contra el LLM.
- No se versionan secretos: usar `.env` local a partir de [.env.example](.env.example).

Ver [docs/security.md](docs/security.md) y [docs/development.md](docs/development.md).

## 12. Referencias principales

- Bohannon, D. *Invoke-Obfuscation*. https://github.com/danielbohannon/Invoke-Obfuscation
- Bohannon, D. y Holmes, L. *Revoke-Obfuscation*. https://github.com/danielbohannon/Revoke-Obfuscation
- Fa2y. *Malicious-PowerShell-Dataset*. https://github.com/Fa2y/Malicious-PowerShell-Dataset
- Fang, Y., Zhou, X. y Huang, C. *Effective method for detecting malicious PowerShell scripts based on hybrid features*. Neurocomputing, 448, 2021 (MPSD). https://github.com/das-lab/mpsd
- Microsoft. *Azure PowerShell documentation samples*. https://github.com/Azure-Samples/azure-docs-powershell-samples
- MITRE. *ATT&CK STIX Data*. https://github.com/mitre-attack/attack-stix-data
- MITRE ATT&CK — T1059.001 Command and Scripting Interpreter: PowerShell. https://attack.mitre.org/techniques/T1059/001/
- Ollama. https://ollama.com

Análisis de fuentes de datos en [docs/dataset_sources.md](docs/dataset_sources.md) y [docs/dataset_audit.md](docs/dataset_audit.md); plan del piloto en [docs/pilot_plan.md](docs/pilot_plan.md).
