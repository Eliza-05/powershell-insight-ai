# Convenciones de desarrollo

## Git

- `main`: rama estable. Solo recibe integraciones revisadas desde `develop`.
- `develop`: rama de desarrollo e integración.
- Ramas de trabajo opcionales a partir de `develop` (`feature/...`, `fix/...`, `docs/...`) para cambios grandes.
- Commits descriptivos, preferentemente con [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `exp:` (experimentos).
- Revisar `git status` y `git diff` antes de cada commit.
- No subir secretos, archivos `.env`, muestras externas ni artefactos de modelos.
- No usar operaciones destructivas (`push --force`, `reset --hard`, reescritura de historial) sin acuerdo explícito del equipo.

## Backend (Python)

- Tipado estático (type hints) siempre que sea posible.
- Separación por responsabilidades según [architecture.md](architecture.md): `api` orquesta, `services` analiza, `schemas` define contratos, `core` configura.
- Los servicios de análisis no dependen de FastAPI, para poder reutilizarlos en `experiments/` y probarlos aisladamente.
- Pruebas con Pytest en `backend/tests/`, usando únicamente muestras inertes.
- Ningún código ejecuta el contenido de un script analizado ([security.md](security.md)).

## Frontend (React + TypeScript)

- Componentes reutilizables y tipados.
- Separación entre componentes de presentación (`components/`, `pages/`) y acceso a la API (`services/`).
- Los tipos compartidos con el backend se reflejan en `types/`.
- No incluir lógica de desofuscación ni credenciales en el navegador.
- Mostrar el código analizado como texto, nunca como HTML interpretado.

## Investigación

- **Reproducibilidad:** cada ejecución experimental referencia una configuración versionada en `experiments/configurations/`.
- **Trazabilidad de datasets:** cada muestra se identifica por su hash SHA-256, fuente y versión de la fuente en `datasets/metadata/`.
- **Versiones de modelos:** registrar nombre, etiqueta y digest del modelo en Ollama, y los parámetros de inferencia.
- **Separación de datos:** desarrollo y evaluación en conjuntos distintos, separados por familias ([methodology.md](methodology.md)).
- **Integridad:** no modificar el conjunto de evaluación final, la taxonomía ni los prompts después de su congelación para mejorar resultados.
- **Resultados:** solo se versionan resultados pequeños, revisados y reproducibles.
