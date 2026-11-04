# Ejecutar PowerShell Insight AI en Windows

MVP local de Fase 3: FastAPI + React 19 / Vite 8 / TypeScript, sobre los pipelines existentes.
Qwen3.5 sigue provisional. Para demostrar la UI con A **no necesitas Ollama**.

## Preparar el entorno

Desde la raíz del repositorio, con Python 3.13 y Node 24 instalados:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-app.txt
npm.cmd --prefix frontend ci
```

Si `.venv` ya existe, reutilízalo y omite su creación. `requirements-app.txt` añade las
dependencias web y conserva el archivo histórico del piloto. `package-lock.json` fija
las dependencias del frontend. Se usa `npm.cmd` para no depender de permisos de ejecución
de `npm.ps1`. No hacen falta instalaciones globales, cambios de ExecutionPolicy ni cuentas.

## Desarrollo: dos terminales

Terminal del backend, desde raíz:

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

Terminal del frontend, desde raíz:

```powershell
npm.cmd --prefix frontend run dev
```

Abrir **http://127.0.0.1:5173**. Vite redirige `/api` a `127.0.0.1:8000`.
Las dos aplicaciones escuchan solo en loopback. Finalizar cada una con Ctrl+C en su terminal.
No iniciar varios workers de Uvicorn para este MVP: los límites de admisión HTTP son por proceso;
la exclusión de inferencia de Fase 2 sigue siendo compartida mediante lock del sistema operativo.

## Demo con un solo servidor

```powershell
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

Abrir **http://127.0.0.1:8000**. FastAPI sirve solo `frontend/dist`, además de la API.
Construir antes de iniciar el backend: el montaje de archivos se decide al arrancar.
Si construyes el frontend después, reinicia tu proceso de backend para habilitar ese montaje.
No se publica el repositorio, fuentes de Python ni directorios de datasets.

## Configuración

La aplicación usa los defaults de `PipelineSettings`: modelo único `qwen3.5:4b-q4_K_M`,
digest autorizado, Ollama `127.0.0.1:11434`, entrada máxima 65.536 bytes UTF-8, contexto 8192,
salida máxima 2048, CPU, `think=false`. No descarga pesos ni inicia/cierra Ollama automáticamente.
El usuario conserva el control de su aplicación local de Ollama y de los modelos residentes.

Variable opcional del backend:

| Variable | Uso |
|---|---|
| `PSI_PIPELINE_SETTINGS` | Ruta a un JSON validado por `PipelineSettings`; omitir para defaults |

Ejemplo de un archivo propio `pipeline.local.json` (ignorado por Git por su sufijo):

```json
{"timeout_seconds": 180, "max_input_bytes": 32768, "options": {"num_thread": 8}}
```

```powershell
$env:PSI_PIPELINE_SETTINGS = (Resolve-Path .\pipeline.local.json).Path
```

Iniciar luego el backend con el comando anterior. Se pueden aumentar márgenes, nunca rebajarlos
por debajo de los mínimos de Fase 2. Modelo/digest siguen fijados al candidato autorizado.
La app no carga `.env` implícitamente; [.env.example](../.env.example) enumera solo lo que se usa.
No existen secretos frontend ni `VITE_*` obligatorias: todas las peticiones usan `/api` relativo.
Puertos soportados de la UI/API: 5173/8000; sus orígenes locales están permitidos explícitamente.

## Usar el estudio

1. Pega texto o elige **Cargar archivo** (`.ps1` o `.txt`, UTF-8). Un BOM UTF-8 se interpreta
   como marcador de codificación; se analiza el texto, no el hash binario del archivo en disco.
   **Usar ejemplo** carga texto sintético propio, sin analizarlo automáticamente.
2. Selecciona A, B, C o comparación. A es el modo inicial y no consulta Ollama.
3. Pulsa **Analizar script** / **Comparar A/B/C**, o Ctrl+Enter desde el editor.
4. Explora Hallazgos, Evidencias, Recuperación y Detalles. **Ver origen** selecciona el ancla
   en el texto original. La conversión de coordenadas contempla UTF-16 del navegador, Unicode
   no BMP y normalización de saltos CRLF del textarea; no modifica el texto enviado al motor.
5. En comparación, selecciona cada columna para abrir su detalle. Las etiquetas diferentes
   se marcan visualmente; eso no mide precisión ni calidad científica.
6. Exporta JSON si quieres conservarlo. El export contiene fuente, peticiones y respuestas:
   tú controlas el destino. No hay historial, almacenamiento automático de muestras ni base de datos.

El botón de estado en el encabezado muestra API, Ollama, modelo, digest y recursos en cualquier
ancho de pantalla; el sidebar añade acceso en escritorio. **Actualizar estado** es una lectura,
no una inferencia. El toggle claro/oscuro persiste exclusivamente `psi-theme` en localStorage.
La guía contextual explica modos, taxonomía, incertidumbre, modelo provisional y Fase 4 pendiente.

## Interpretar estados

| Estado de resultado | Significado |
|---|---|
| Completado | Procesamiento y comprobaciones estructurales terminados; no aprobación semántica |
| Parcial | Se conservan límites, indicadores o contenido desconocido |
| Entrada rechazada | Texto no admisible |
| No disponible | Servicio, modelo, recursos o circuito impiden inferir |
| Respuesta rechazada | Error de respuesta/validación; no se publican hallazgos LLM aceptados |

Las técnicas de 1A y las declaradas por el LLM se etiquetan por separado. A conserva reglas,
evidencias e indicadores. B/C conservan la autoría del modelo, su incertidumbre y riesgo declarado.
La recuperación determinista es distinta de `recovered_content` del modelo, que se muestra como
no verificado. Un resultado sin etiquetas no prueba que el script sea benigno.

## Memoria, tiempos y errores

B/C conservan los controles de Fase 2: digest exacto, un modelo residente, una inferencia a la
vez, reserva de carga y margen mínimo de 2 GiB de RAM y compromiso, monitor de un segundo y
timeout absoluto. La API limita lecturas auxiliares de Ollama a 3 s por endpoint y mantiene
el timeout configurado de inferencia, máximo 300 s. El frontend permite hasta 660 s para ABC.
No hay reintentos automáticos ni reparación de JSON.

La admisión web permite hasta dos A y una petición B/C/ABC simultáneas, sin cola ilimitada.
Un segundo trabajo LLM recibe 409. La API sigue respondiendo a health y A mientras infiere.
Cerrar una pestaña o agotar el timeout del navegador no certifica que el servidor haya terminado;
revisar estado antes de reenviar. La API no incluye un botón de cancelación que prometa una
cancelación no comprobada. El circuito persistente de Fase 2 requiere revisión explícita tras
interrupciones; ver [procedimiento](phase2_integration.md#límites-y-recursos).

Errores útiles: conexión API → iniciar backend; Ollama ausente → A sigue disponible; memoria
insuficiente → B/C devuelven indisponibilidad; contexto excesivo → texto/evidencia completos
rechazados, sin recorte silencioso. No se cierran aplicaciones ni se cambian configuraciones
globales para liberar memoria. No enviar muestras externas potencialmente peligrosas sin el
entorno aislado que el proyecto aún tiene pendiente.

## API

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/api/health` | Estado de API independiente de Ollama y actividad |
| GET | `/api/metadata` | Versión, esquema y estado metodológico |
| GET | `/api/capabilities` | Modos, límites, modelo y parámetros |
| GET | `/api/ollama/status` | Disponibilidad/digest/recursos, sin inferir |
| POST | `/api/analyze/A` | `PipelineResult` determinista |
| POST | `/api/analyze/B` | `PipelineResult` LLM original |
| POST | `/api/analyze/C` | `PipelineResult` LLM + 1A |
| POST | `/api/compare` | `ComparisonResult`, tres ejecuciones independientes |
| GET | `/openapi.json` | Esquema OpenAPI reutilizable |

POST acepta **solo** `{"script":"texto original"}`. No recibe modelos, parámetros, etiquetas,
referencias o historial desde el navegador. Un resultado de pipeline con `status=error` o
`unavailable` puede viajar en HTTP 200: la petición fue atendida y su estado está en el contrato.
Errores de payload/admisión usan HTTP 413/415/422/409 y `error.code/message/details`.
El cuerpo HTTP se limita antes de parsear JSON, además del límite en bytes del texto.
Orígenes no permitidos se rechazan y los hosts se restringen a loopback. No es un servicio
multiusuario autenticado ni está preparado para exposición pública.

`/docs` y `/redoc` no están habilitados: se evita depender de scripts CDN para documentación
interactiva. La guía contextual y OpenAPI JSON están disponibles sin servicios externos.

## Pruebas y construcción

Desde raíz:

```powershell
$phase3Temp = Join-Path $env:TEMP ('ps-insight-phase3-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider backend/tests --basetemp "$phase3Temp" --tb=short
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
```

Con el backend corriendo en 8000, la prueba React + HTTP real usa **solo A**, cero inferencias:

```powershell
npm.cmd --prefix frontend run test:integration
```

Las pruebas B/C de la API y los componentes usan transportes/respuestas sintéticas; no cargan
el modelo ni tocan selección. No ejecutar el harness real de Fase 2 como parte de estas pruebas.
La revisión visual manual recomendada es abrir claro/oscuro en 1440, 1024 y 390 px, verificar
scroll, foco, diálogo, carga y comparación. En esta entrega no pudo hacerse mediante navegador
automatizado porque su host no estaba disponible; no se presentan capturas o una certificación
visual inexistentes. [Estado y evidencia de cierre](phase3_closure.md).
