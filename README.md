# PowerShell Insight AI

LLM-powered static analysis and deobfuscation of PowerShell scripts for cybersecurity research.

**Título académico:** Sistema inteligente de análisis estático, desofuscación y caracterización de scripts PowerShell mediante un modelo de lenguaje local.

Proyecto final de la asignatura **Ciberinteligencia**.

> **Estado: fase inicial.** El repositorio contiene únicamente la estructura base y la documentación del proyecto. El sistema de análisis, la API, la interfaz web y la integración con el LLM **todavía no están implementados**. No existen resultados experimentales.

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
- Identificación determinista de comportamientos según una [taxonomía propia](docs/behavior_taxonomy.md).
- Explicación asistida por un LLM local, con salida estructurada.
- Validación y trazabilidad de evidencias (cada hallazgo vinculado a fragmentos del script).
- Mapeo opcional a técnicas de MITRE ATT&CK.
- Módulo de evaluación experimental para comparar configuraciones.

## 5. Stack tecnológico

| Componente | Tecnología |
|---|---|
| Frontend | React + TypeScript + Vite |
| Estilos | Tailwind CSS |
| Editor de código | Monaco Editor (candidato) |
| Backend | Python + FastAPI |
| LLM | Ollama (local) |
| Modelo candidato | Qwen2.5-Coder 7B |
| Validación estructurada | Pydantic |
| Análisis experimental | Pandas + scikit-learn |
| Pruebas de backend | Pytest |
| MITRE ATT&CK | STIX 2.1 (opcional) |

Ninguna de estas tecnologías está instalada todavía.

## 6. Arquitectura general

```text
Frontend React ──► API FastAPI ──► Desofuscación estática ──► Detección por reglas
                                                                    │
                     Respuesta estructurada ◄── Validación de ◄── LLM local (Ollama)
                                                evidencias
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
│   │       ├── detection/            # Motor determinista de comportamientos
│   │       ├── llm/                  # Integración con Ollama
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

Se evaluarán la identificación de comportamientos (precision, recall, F1), la calidad explicativa (validez de evidencias, afirmaciones no respaldadas) y la recuperación de código. Detalle en [docs/methodology.md](docs/methodology.md).

## 9. Estado actual

| Elemento | Estado |
|---|---|
| Estructura del repositorio | ✅ Creada |
| Documentación inicial | ✅ Creada |
| Validación de datasets | ⏳ Pendiente |
| Validación del modelo en Ollama | ⏳ Pendiente |
| Motor de desofuscación | ⏳ No iniciado |
| Motor de reglas | ⏳ No iniciado |
| Integración LLM | ⏳ No iniciado |
| Frontend | ⏳ No iniciado |
| Experimentos | ⏳ No iniciados |

## 10. Próximas fases

Ver [docs/roadmap.md](docs/roadmap.md): validación de datasets y modelo → motor estático y reglas → integración del LLM → frontend → experimentos → informe y demostración.

## 11. Precauciones de seguridad

- El sistema realiza **exclusivamente análisis estático**: nunca ejecuta ni evalúa scripts.
- El repositorio **no contiene malware real**. Las muestras externas se manejan fuera del repositorio, en entornos aislados, y los directorios correspondientes están excluidos por `.gitignore`.
- El contenido de los scripts (comentarios, cadenas) se trata como entrada no confiable, incluida la prevención de *prompt injection* contra el LLM.
- No se versionan secretos: usar `.env` local a partir de [.env.example](.env.example).

Ver [docs/security.md](docs/security.md) y [docs/development.md](docs/development.md).

## 12. Referencias principales

- Bohannon, D. *Invoke-Obfuscation*. https://github.com/danielbohannon/Invoke-Obfuscation
- Bohannon, D. y Holmes, L. *Revoke-Obfuscation*. https://github.com/danielbohannon/Revoke-Obfuscation
- Fa2y. *Malicious-PowerShell-Dataset*. https://github.com/Fa2y/Malicious-PowerShell-Dataset
- MITRE. *ATT&CK STIX Data*. https://github.com/mitre-attack/attack-stix-data
- MITRE ATT&CK — T1059.001 Command and Scripting Interpreter: PowerShell. https://attack.mitre.org/techniques/T1059/001/
- Ollama. https://ollama.com

Análisis de fuentes de datos en [docs/dataset_sources.md](docs/dataset_sources.md).
