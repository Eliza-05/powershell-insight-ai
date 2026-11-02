# Configuración del entorno local en Windows

Guía para preparar PowerShell Insight AI en cualquier equipo Windows 10/11. Solo cubre lo que existe hoy: el piloto de la Fase 0B (cliente de Ollama, validación con Pydantic y pruebas con Pytest). La API, el frontend y los motores de análisis todavía no están implementados.

Todos los comandos se ejecutan en PowerShell. Las rutas de ejemplo son orientativas: el proyecto no depende de ninguna ubicación concreta.

## 1. Requisitos

| Componente | Versión de referencia | Notas |
|---|---|---|
| Windows | 10 u 11, 64 bits | Instalación por usuario; no se requieren privilegios de administrador |
| Python | 3.13.3 | Versión con la que se fijaron las dependencias. Otras 3.13.x deberían funcionar |
| Git | Cualquier versión reciente | |
| Ollama | 0.40.13 | Versión usada en el piloto |
| Modelo | `qwen2.5-coder:7b` (Q4_K_M) | ~4,7 GB en disco; ~5 GB de RAM al cargarse. Funciona solo con CPU |
| Espacio libre | ≥ 8 GB | Modelo + entorno virtual + margen |

## 2. Clonar el repositorio

Elige cualquier carpeta de trabajo:

```powershell
git clone https://github.com/Eliza-05/powershell-insight-ai.git
cd powershell-insight-ai
git switch develop
```

Todos los pasos siguientes asumen que la terminal está en la raíz del repositorio.

## 3. Crear el entorno virtual `.venv`

El entorno virtual vive dentro del repositorio, en `.venv/`, que está excluido por `.gitignore`.

```powershell
py -3.13 -m venv .venv          # o: python -m venv .venv
.\.venv\Scripts\python.exe --version
```

Un entorno virtual contiene rutas absolutas de la máquina donde se creó: no se copia entre equipos ni carpetas. Si el repositorio cambia de ubicación, se borra `.venv` y se vuelve a crear.

Activarlo es opcional. Si se quiere activar:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script de activación, basta con permitirlo para el usuario actual (`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`) o, sin cambiar nada, invocar siempre `.\.venv\Scripts\python.exe` directamente, como hace esta guía.

## 4. Instalar dependencias

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-pilot.txt
.\.venv\Scripts\python.exe -m pip freeze
```

`backend/requirements-pilot.txt` fija todas las versiones (directas y transitivas). No actualices paquetes sin registrarlo: el piloto debe poder reproducirse con las mismas versiones.

## 5. Instalar Ollama

1. Descarga el instalador oficial desde <https://ollama.com/download/windows> (`OllamaSetup.exe`).
2. Opcional: comprueba la firma digital (Propiedades → Firmas digitales, firmante *Ollama Inc.*) o con `Get-AuthenticodeSignature .\OllamaSetup.exe`.
3. Ejecuta el instalador. Se instala por usuario en `%LOCALAPPDATA%\Programs\Ollama` y arranca un icono en la bandeja del sistema.
4. Abre una terminal nueva y comprueba:

```powershell
ollama --version
```

Documentación oficial: <https://docs.ollama.com/windows>.

## 6. Ubicación de los modelos (opcional)

Por defecto Ollama guarda los modelos en `%USERPROFILE%\.ollama\models`. Para la mayoría de usuarios no hace falta cambiar nada.

Si prefieres otra carpeta (por ejemplo, otro disco o una carpeta de recursos locales junto al repositorio), define la variable de entorno de usuario `OLLAMA_MODELS` **antes** de descargar el modelo:

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_MODELS', 'D:\ruta\que\elijas\ollama-models', 'User')
```

O bien desde *Configuración → Editar las variables de entorno de esta cuenta*.

Después:

1. Cierra Ollama desde el icono de la bandeja (*Quit Ollama*).
2. Vuelve a abrirlo desde el menú Inicio, para que el proceso lea la variable nueva.
3. Comprueba la ruta efectiva en el log del servidor:

```powershell
Select-String "$env:LOCALAPPDATA\Ollama\server.log" -Pattern 'OLLAMA_MODELS:' | Select-Object -Last 1
```

Recomendaciones:

- La carpeta de modelos debe quedar **fuera del repositorio**. Una opción ordenada es una carpeta hermana, por ejemplo `..\<NombreProyecto>-Local\ollama-models`.
- Evita carpetas sincronizadas en la nube (OneDrive, Dropbox…): son varios GB que cambian poco y la sincronización puede bloquear archivos.
- Si ya tenías el modelo descargado, puedes copiar la carpeta `models` completa (`blobs`, `manifests` y el resto) a la nueva ubicación en lugar de volver a descargarlo. El nombre de cada archivo de `blobs` es su SHA-256, lo que permite verificar la copia con `Get-FileHash`.

## 7. Descargar Qwen2.5-Coder 7B

```powershell
ollama pull qwen2.5-coder:7b
ollama list
ollama show qwen2.5-coder:7b
```

El digest de referencia usado en el piloto es:

```text
dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364
```

Si `ollama list` muestra un ID distinto de `dae161e27b0e`, el tag se ha actualizado en el registro y los resultados no serán directamente comparables con los del piloto. Regístralo.

## 8. Comprobar la API local

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/version
(Invoke-RestMethod http://127.0.0.1:11434/api/tags).models | Select-Object name, digest
Get-NetTCPConnection -LocalPort 11434 -State Listen | Select-Object LocalAddress, LocalPort
```

`LocalAddress` debe ser `127.0.0.1`. No definas `OLLAMA_HOST=0.0.0.0`: la herramienta es de uso local y la API de Ollama no tiene autenticación ([security.md](security.md)).

Prueba de humo (no analiza ningún script):

```powershell
ollama run qwen2.5-coder:7b "Reply with exactly the word: OK"
```

## 9. Variables de entorno

| Variable | Ámbito | Uso |
|---|---|---|
| `OLLAMA_MODELS` | Usuario de Windows (opcional) | Carpeta de modelos de Ollama. Ver sección 6 |
| `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `API_HOST`, … | Archivo `.env` local | Plantilla en [.env.example](../.env.example), reservada para la futura API. Copiar a `.env` (`Copy-Item .env.example .env`); `.env` nunca se versiona |

El piloto de la Fase 0B **no lee variables de entorno**: toma el host de Ollama, el modelo, el prompt y las opciones de inferencia de la configuración versionada [experiments/configurations/pilot_v1.json](../experiments/configurations/pilot_v1.json). Esa configuración está congelada; para usar otro host o modelo se crea una copia con otro `config_id` y se pasa con `--config`.

## 10. Ejecutar las pruebas automatizadas

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ..
```

También funciona desde la raíz: `.\.venv\Scripts\python.exe -m pytest -q backend\tests`.

Las pruebas no llaman a Ollama (usan un cliente simulado) y no ejecutan ningún script PowerShell. `backend/pytest.ini` añade `backend/` y la raíz del repositorio al `sys.path`, por lo que no hace falta instalar el paquete.

## 11. Ejecutar el piloto experimental

Requiere Ollama en marcha y el modelo descargado. En CPU, las 24 ejecuciones (P1–P8 × 3) tardan varias horas.

```powershell
.\.venv\Scripts\python.exe experiments\run_pilot.py
```

- Los resultados se escriben en una carpeta nueva `experiments/results/pilot/<config_id>_<fecha>/`; nunca se sobrescribe una ejecución anterior.
- Para recalcular métricas de una ejecución existente sin volver a llamar al modelo, indica una carpeta de salida **nueva**. La carpeta de origen solo se lee; el comando se niega a escribir en una carpeta no vacía o con derivados existentes:

```powershell
.\.venv\Scripts\python.exe experiments\run_pilot.py --evaluate-only experiments\results\pilot\<carpeta> --out-dir experiments\results\pilot\derived\<carpeta_nueva>
```

- Para comprobar que los resultados históricos no se han alterado (en Git Bash):

```bash
cd experiments/results/pilot && sha256sum -c pilot-v1_20261101T001806Z.SHA256SUMS
```

- `--help` muestra todas las opciones.

Las muestras de `datasets/safe_samples/` se leen como texto y se envían al modelo. **Nunca se ejecutan.**

## 12. Qué no debe incorporarse a Git

`.gitignore` ya excluye estos elementos. No los fuerces con `git add -f`:

- `.venv/`, `venv/` y cualquier entorno virtual.
- `__pycache__/`, `*.pyc`, `.pytest_cache/`.
- Modelos y sus blobs (`*.gguf`, `*.bin`, `models/`) y cualquier carpeta de `OLLAMA_MODELS`.
- Cachés y temporales (`experiments/cache/`, `*.tmp`, `logs/`).
- `.env` y cualquier secreto.
- Muestras externas o potencialmente maliciosas (`datasets/raw/`, `datasets/quarantine/`, comprimidos).

Comprobación rápida:

```powershell
git check-ignore -v .venv
git status --short
```

## 13. Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `ollama` no se reconoce como comando | La terminal se abrió antes de instalar Ollama | Abre una terminal nueva o usa `& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"` |
| `No se puede establecer una conexión… 11434` | El servidor de Ollama no está en marcha | Abre Ollama desde el menú Inicio y revisa `%LOCALAPPDATA%\Ollama\server.log` |
| `model "qwen2.5-coder:7b" not found` tras cambiar `OLLAMA_MODELS` | Ollama no se reinició, o la carpeta nueva está vacía o incompleta | Cierra Ollama desde la bandeja y ábrelo de nuevo; comprueba la ruta en `server.log` y que existan `blobs` y `manifests` |
| La variable `OLLAMA_MODELS` no se aplica | El proceso hereda el entorno antiguo | Cerrar sesión de Windows y volver a entrar es la forma más segura de que todos los procesos la lean |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Política de ejecución de PowerShell | Usa `.\.venv\Scripts\python.exe` directamente o `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ModuleNotFoundError: No module named 'ollama'` | Se usa un Python distinto al de `.venv` | Usa `.\.venv\Scripts\python.exe` y repite la instalación de dependencias |
| `.venv` deja de funcionar tras mover o renombrar la carpeta del repositorio | El entorno virtual guarda rutas absolutas | Borra `.venv` y vuelve a crearla (secciones 3 y 4) |
| Respuestas muy lentas | Inferencia solo en CPU | Esperado en equipos sin GPU compatible. Cierra otras aplicaciones pesadas; `ollama ps` muestra si el modelo está en CPU o GPU |
| `ollama list` muestra un ID distinto de `dae161e27b0e` | El tag se actualizó en el registro | Los resultados no son comparables con el piloto. Registra el digest nuevo |
