# Cierre Git

**Responsable de la integración:** Karol. **Preparación:** Claude (IA). La sesión de Claude no tiene credenciales de GitHub, así que Karol hace los `push` y el merge desde su copia.

## 1. Ramas y SHA

| Elemento | SHA |
|---|---|
| `develop` antes del cierre (publicado) | `2c10019dccff0e261752f032ac156c8638ab7f65` |
| Base de `integration/final-validation` recibida el 9 nov | `a3ba71eea3a264b16b11c090b0e1f03b1a53b5f1` |
| **SHA científico** (código desplegado en la campaña 3) | `41330339abc5ba8a73ca6b595c9ed4396d275e82` |
| Último commit de `integration/final-validation` | El que contiene este archivo (ver el recibo externo) |
| SHA final de `develop` (merge) | Se registra en el recibo externo `RECIBO_CIERRE_GIT.txt`, porque un commit no puede incluir su propio SHA |

Los commits posteriores a `4133033` solo cambian documentación y evidencia publicable. No modifican código, el protocolo congelado ni los archivos que cubre el manifiesto del candidato. Por eso los resultados corresponden al SHA científico, no a commits posteriores.

## 2. Commits del cierre (sobre `a3ba71e`)

| Commit | Tipo | Resumen |
|---|---|---|
| `ec63f7f` | fix | CTX-01: presupuesto de contexto escalado; regla única para el adaptador y `prepare`; comprobación posterior; 11 pruebas |
| `9a18262` | docs+code | Protocolo prospectivo; `refresh_candidate` cubre el protocolo, CTX-01 y `requirements-pilot`; 1 prueba |
| `4133033` | docs | Protocolo aprobado; autoría de las referencias declarada (**SHA científico**) |
| `2dd83bb` | docs | Informe técnico, evidencia del entorno GCP y validación del frontend |
| `f17c343` | docs | Guía de demo (borrador) y herramientas de revisión personal |
| `488638f` | docs | Campaña 3 completa, H1 evaluada, incidentes 1–2 |
| `c357fb5`, `2465e41` | docs | H2 evaluada; corrección de un recuento |
| `09f78c6` | docs | README final e índice de evidencias |
| `3c82616` | docs | Demo reproducida, informe técnico final y respaldo indexado |
| (este) | docs | Cierre Git |

Todos los commits tienen como autora a Karol, con la línea `Co-Authored-By: Claude`.

## 3. Pruebas sobre el resultado integrado

- **Antes del merge:**
  - Selección segura del plan (§16) más CTX-01: 779 aprobadas en GCP nativo (`4133033`).
  - Frontend: 141 pruebas, build, integración (11) y navegador (20/10/87).
- **Después del merge:** se repite la misma selección sobre el árbol integrado (§4).
- No se ejecuta la suite científica completa (`pytest backend/tests`), porque lee material reservado y crea propuestas.

## 4. Procedimiento de merge

El repositorio integra por PR (así se hicieron #1 y #2). Pasos:

1. Publicar la rama de integración:
   `git -c remote.origin.mirror=false push origin integration/final-validation`
2. En GitHub, abrir un PR de `integration/final-validation` hacia `develop` y revisar el diff completo. Incluye los commits del 9 nov (`18f772e`–`a3ba71e`) y los del cierre; estos últimos tocan 3 archivos de backend, `experiments/phase4/prepare.py`, 1 archivo de pruebas y documentación.
3. Hacer **merge commit**, sin squash, para conservar los SHA, incluido el científico.
4. Comprobar en remoto y registrar en `RECIBO_CIERRE_GIT.txt` (fuera de Git o en un commit documental posterior):
   `git ls-remote origin refs/heads/develop refs/heads/integration/final-validation`

Si no hay conflictos esperables, el merge es directo: `develop` (`2c10019`) es ancestro de la rama. Si aparecieran conflictos, se resuelven revisando cada uno, sin aceptar "ours" o "theirs" globalmente, y se documentan aquí.

## 5. Material que no entra en Git

- Casos y referencias F4, solicitudes, salidas crudas, ledger, autorizaciones y revisiones personales.
- Claves (`.pem` y la clave SSH de GCP), binding operativo, respaldos `.tgz` y `frontend/dist`.

Su ubicación y sus hashes están en `EVIDENCIAS.md` §Evidencia del cierre. Se revisó que los archivos nuevos de `docs/cierre-modelo-fase4/` no contengan F4, claves ni IP públicas.
