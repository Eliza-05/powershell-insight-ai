# Informe técnico del cierre — PowerShell Insight AI

**Rama:** `integration/final-validation`. **Responsable:** Karol. **Redacción y ejecución técnica:** Claude (IA), a petición de Karol.
**Vigencia:** cada afirmación indica fecha, SHA y entorno. Las capturas anteriores (AWS, `18f772e` y `7fc29f8`) se citan como históricas, no como validación vigente.

## 1. Sistema

- **Aplicación 0.3.0:** backend FastAPI/Python, frontend React/TypeScript/Vite. El análisis es estático: ningún script PowerShell se ejecuta.
- **A:** desofuscación 1A y reglas deterministas 1B, sin LLM.
- **B y C:** usan el LLM local `qwen3-coder:30b` a través de Ollama en loopback. B recibe el original; C recibe además la recuperación 1A verificada. Los dos modos comparten política, parámetros y postprocesamiento.
- **Perfil:** `PSI_LLM_PROFILE=qwen3coder-v2`. Sin esa variable se usa el prototipo histórico Qwen14. Un valor desconocido hace fallar el arranque, sin fallback.
- **Capas deterministas comunes a B y C** (`v2-deterministic-layers-2`):
  - Antes del LLM, los comentarios se reemplazan por espacios (`comment-blanking-v2-diagnostics`). Los offsets se conservan y las regiones inciertas se informan.
  - Después del LLM, un verificador conservador de evidencia (`evidence-check-v2-bounded`) descarta etiquetas no verificadas sin cambiar el riesgo que dio el modelo.
- **Política v2:** SHA-256 del texto normalizado `53d4cc36…`. La estrategia se niega a funcionar si el texto cambia.
- La configuración completa está en `PROTOCOLO_FASE4.md` §3.

## 2. Cambios de esta etapa (sobre `a3ba71e`)

| Commit | Cambio | Pruebas |
|---|---|---|
| `ec63f7f` | **CTX-01:** presupuesto de contexto escalado (0,5 tokens/byte) para `qwen3coder-v2`, con una regla única para el adaptador y `prepare.py`. La comprobación posterior no publica respuestas cuya entrada real invada la reserva de salida. Los perfiles históricos no cambian | 11 nuevas; selección segura: 767 → 778 |
| `9a18262` | `PROTOCOLO_FASE4.md` prospectivo. `refresh_candidate` cubre el protocolo, la enmienda CTX-01 y `requirements-pilot.txt` | +1 (779) |
| `4133033` | Protocolo aprobado por Karol; declarada la autoría de las referencias | — |

El diagnóstico, los datos de calibración (solo desarrollo, nunca F4) y la aprobación están en `CTX01_DIAGNOSTICO_Y_ENMIENDA.md`.

## 3. Infraestructura

- **AWS (histórico):** la EC2 de `7fc29f8` dejó de estar disponible el 10 nov 2026, cuando AWS cerró la cuenta por una verificación de pago pendiente. Las copias, el binding y los logs recuperados de esa etapa existen solo donde se guardaron localmente (`logs/` del workspace original, ver `EVIDENCIAS.md`). Esta etapa no los modificó.
- **Google Cloud (vigente):** proyecto `psi-cierre`, instancia `psi-cierre`, e2-standard-8 (8 vCPU, 32 GB), us-central1-c, disco balanceado de 60 GB.
  - Sistema: Ubuntu 24.04.5 LTS, kernel 7.0.0-1017-gcp.
  - Python 3.13.18 en un venv propio (uv), con las dependencias fijadas de `requirements-app.txt` y `requirements-pilot.txt`. `pip check` sin conflictos.
  - Ollama 0.40.16, solo CPU, escuchando únicamente en `127.0.0.1:11434`. El modelo se descargó una vez y su digest coincide: `06c1097e…`.
  - El acceso es por SSH con una clave dedicada; no se abrieron puertos adicionales.
  - Evidencia: `evidencias-publicables/validacion-final/ENTORNO_GCP_Y_CANDIDATO.json`.
- **Binding del almacén del modelo** (`linux-model-filesystem-binding-v1`):
  - El almacén `/usr/share/ollama/.ollama/models` pertenece al usuario `ollama`; el usuario SSH no puede leerlo.
  - La evidencia de metadatos se obtuvo con consultas de solo lectura (`sudo realpath/stat/findmnt/du`, sin leer los blobs). Su SHA-256 es `61e6111e…`. El binding (`65d5dc7c…`) usa `/usr/share` como ancla accesible.
  - `native_state` lo verificó sin generar texto.
  - Ese uso de sudo de solo lectura forma parte de la configuración inicial de una VM propia y queda declarado aquí.
- **Diferencias con el laboratorio:** Ollama 0.40.16, frente a 0.40.14 en el laboratorio y 0.40.15 en AWS; la máquina es una E2 en lugar de t3a/t2. Los parámetros de inferencia no cambian.

## 4. Despliegue

- Cada SHA se despliega en una copia nueva (`~/psi-final-<sha>`, desde un bundle verificado por SHA-256).
- La copia científica `~/psi-sci-4133033` se creó con `git archive` del commit aprobado, excluyendo `artifacts/phase4_preparation`. Ese directorio contiene el plan histórico Qwen14, que `prepare` no puede sobrescribir y que sigue íntegro en Git. Hash del archivo: `db1b155e…`; 1346 archivos.
- Las copias anteriores y el laboratorio R1–R7 se conservan.

## 5. Pruebas

| Fecha (UTC) | SHA | Entorno | Prueba | Resultado |
|---|---|---|---|---|
| 2026-11-10 05:2x | `a3ba71e` + CTX-01 | Contenedor | Selección segura del plan (§16) | 767 aprobadas (base) |
| 2026-11-10 15:12 | `ec63f7f` | GCP nativo | Selección segura + CTX-01 | 778 aprobadas, exit 0 |
| 2026-11-10 15:18 | `4133033` | GCP nativo | Igual | **779 aprobadas, 0 fallos/errores/omitidas** (junit `1f22cfdc…`) |
| 2026-11-10 15:4x | `4133033` | Contenedor | Frontend: vitest | 141 aprobadas |
| 〃 | 〃 | 〃 | `npm run build` (tsc + vite) | OK |
| 〃 | 〃 | 〃 | Integración HTTP+React contra el servidor sintético | 11 aprobadas |
| 〃 | 〃 | 〃 | Navegador: `integrated.mjs` / `--zoom200` / `verify.mjs --comparison-layout` | 20 / 10 / 87 casos, 0 fallos |

Las pruebas de navegador se ejecutaron con Chromium en modo headless, como usuario no root y con la sandbox activa. El primer intento como root fue rechazado por la sandbox y no se desactivó ninguna protección. Todas las pruebas B/C de esta tabla usan un transporte sintético; ninguna contacta el modelo real. Evidencia: `validacion-final/VALIDACION_FRONTEND_SINTETICA.json`.

No se ejecutó `pytest backend/tests` completo, porque la suite científica lee material reservado y crea propuestas.

## 6. Preparación del candidato (Fase 4)

Autorizada por Karol (2026-11-10 10:37 −05:00) y ejecutada en `psi-sci-4133033` con el binding:

- `exit 0`: 16 unidades, 32 solicitudes, estratos 8/8. La auditoría automática de independencia no encontró duplicados. **0 inferencias.**
- CTX-01 resuelto: 5 de las 32 solicitudes habrían sido rechazadas por la regla de bytes. Con la regla escalada, la mayor usa 3142 de 5632 tokens estimados, un margen de 2490.
- Hash del manifiesto del candidato: `cfc1cc98…`. La lista completa está en `ENTORNO_GCP_Y_CANDIDATO.json`.

## 7. Incidencias

| Incidencia | Tratamiento |
|---|---|
| CTX-01 bloqueaba la preparación | Corregido con la enmienda aprobada, sin usar F4 |
| AWS cerró la cuenta | Migración a GCP antes de congelar nada; documentada en el protocolo §4 |
| `prepare` no puede escribir sobre el plan histórico Qwen14 | Copia científica sin ese directorio; el histórico sigue intacto en Git |
| Chrome como root exige `--no-sandbox` | Se ejecutó como usuario no root, sin desactivar la sandbox |

## 8. Pendiente en este informe

Las secciones de campaña, demostración y SHA final se completan cuando terminen esas etapas. Estado: ver `README.md`.
