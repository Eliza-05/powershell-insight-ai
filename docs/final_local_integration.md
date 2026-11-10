# Integración local final y preparación prospectiva

Esta guía corresponde al perfil definitivo experimental `qwen3coder-v2`. La comprobación local no ejecuta inferencias, muestras PowerShell ni campañas científicas. La elección del modelo no certifica calidad científica. No usar F4-01–F4-16 para desarrollar o probar la integración.

## Perfil efectivo

- Modelo: `qwen3-coder:30b`; digest `06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca`.
- Política v2 normalizada UTF-8/LF: `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081`.
- Bytes de política en el checkout Windows auditado (CRLF): `c17d5b11001eefdd76c5b77538a4265d93ea3fbe35e579cd08f3e7e2bb94949f`. Registrar los bytes efectivos de la infraestructura, sin confundirlos con el texto enviado.
- Estrategia `v2-deterministic-layers-2`; postcheck `evidence-check-v2-bounded`; sanitización `comment-blanking-v2-diagnostics`.
- CPU, temperatura 0, seed 42, contexto 8192, salida máxima 2048, timeout individual 300 s; sin fallback, pull ni reintento automático.
- Ollama exclusivamente en `127.0.0.1:11434`. Configurar el perfil en el entorno del proceso; `.env` no se carga automáticamente. Sin variable se mantiene Qwen14 histórico.
- Reserva de carga en frío más margen: 23968709120 bytes. No se requiere disponer localmente del modelo para las pruebas simuladas.

## Repetir las comprobaciones seguras

Desde la raíz, con las dependencias ya instaladas, sin instalar ni descargar nada:

```powershell
.\.venv\Scripts\python.exe -m pip check
npm.cmd --prefix frontend test -- --cache=false --fsModuleCache=false --configLoader=runner
npm.cmd --prefix frontend run build
```

Suite backend inspeccionada, con un temporal nuevo en cada ejecución:

```powershell
$psiTestTemp = Join-Path $env:TEMP ('psi-backend-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider --basetemp "$psiTestTemp" --tb=short -q backend/tests/pipelines/test_final_integration.py backend/tests/pipelines/test_qwen3coder_v2.py backend/tests/pipelines/test_qwen3coder_regressions.py backend/tests/pipelines/test_pipelines.py backend/tests/api/test_api.py backend/tests/api/test_qwen14_prototype.py backend/tests/pipelines/test_qwen14_exploratory.py backend/tests/pipelines/test_qwen14.py::test_transport_rejects_wrong_model_and_missing_authorization backend/tests/pipelines/test_gemma4_v2.py backend/tests/deobfuscation backend/tests/behavior_detection
```

No sustituir esta selección por toda la suite científica: existen pruebas que crean propuestas/congelaciones o cargan las referencias reservadas. Los fixtures históricos seleccionados copian congelaciones existentes a temporales, sin generar nuevas ni cambiar los originales.

Para levantar **exclusivamente el servidor de prueba** en una terminal separada, usar un puerto libre; no detener el servicio que ya ocupe 8000:

```powershell
$env:PSI_TEST_TEMP = Join-Path $env:TEMP ('psi-http-' + [guid]::NewGuid().ToString('N'))
$env:PSI_TEST_ORIGIN = 'http://127.0.0.1:8765'
$env:PSI_LLM_PROFILE = 'qwen3coder-v2'
.\.venv\Scripts\python.exe -B -m uvicorn tests.api.integration_server:make_app --factory --app-dir backend --host 127.0.0.1 --port 8765 --no-access-log
```

El harness usa FastAPI, AnalysisService, 1A/1B, adaptador y estrategia reales. Sustituye el transporte y la disponibilidad de memoria por valores controlados. Sus endpoints `__test` no forman parte de `app.main`. Sirve el frontend compilado después de sus rutas de prueba. Todas sus salidas son sintéticas; no apunta al Ollama real.

Desde otra terminal, con ese servidor activo:

```powershell
$env:PSI_TEST_URL = 'http://127.0.0.1:8765'
$env:PSI_TEST_SYNTHETIC = '1'
npm.cmd --prefix frontend run test:integration -- --cache=false --fsModuleCache=false --configLoader=runner
node frontend/browser/verify.mjs --comparison-layout
node frontend/browser/integrated.mjs
node frontend/browser/integrated.mjs --zoom200
```

Las pruebas HTTP B/C exigen que `__test/state` confirme el transporte sintético. El navegador nuevo también se niega a despachar B/C sin esa comprobación. Los scripts bloquean destinos externos, usan un perfil Chrome temporal, descargan JSON únicamente en TEMP y cierran ese navegador. No deshabilitan la sandbox de Chrome. El helper usa renderizado por software (`--disable-gpu`), sin cambiar preferencias persistentes. Si el aislamiento de la herramienta impide crear procesos de Chrome, se necesita permitir la ejecución de esa automatización local; no eludirlo desactivando protecciones del equipo.

Finalizar el servidor de prueba con Ctrl+C en su propia terminal. No detener procesos ajenos. Los informes, screenshots y descargas quedan en las rutas TEMP que imprime cada script.

## Presentación y contratos

«Detalles» muestra predicción original, resultado aceptado, riesgo original del modelo, decisiones conservadas/descartadas, citas, spans y limitaciones. Un aviso accesible lleva a ese panel sin iniciar otro análisis. Las advertencias de sanitización parcial son visibles. `evidence_check_incoherent` se presenta como rechazo de publicación, no como benignidad. Respuestas inválidas no se presentan como predicciones vacías.

Los campos nuevos son opcionales para conservar compatibilidad con Qwen14. Los validadores comprueban los datos operativos consumidos por la UI y sus spans antes de renderizar. React los representa como texto. La exportación mantiene la respuesta completa, incluidos raw, decisiones y riesgo original, también para resultados rechazados o anteriores.

El build conserva las fuentes como archivos del mismo origen (`assetsInlineLimit: 0`), compatible con `font-src 'self'` de FastAPI. No se debilitó la CSP para permitir fuentes data:.

## Cambios prospectivos del controlador

El controlador antes fijaba Qwen14 en settings, transporte, adaptador, contexto y `show`. Ahora el módulo `experiments.phase4.profile` enlaza explícitamente el perfil autorizado. Configuraciones históricas sin `llm_profile` siguen siendo Qwen14; una configuración Qwen3 requiere `llm_profile=qwen3coder-v2`, settings completos y bindings de estrategia/política correspondientes. Un perfil o digest incompatible falla, sin fallback.

Preparar contextos B/C y ejecutar el servicio utiliza el mismo builder/estrategia. Se probaron sus requests canónicos con texto sintético, sin cargar el módulo de casos reservados. La preparación importa las referencias solo dentro de la función explícita que las necesita; importar perfil/controlador no carga soluciones.

La nueva ruta conserva 16 unidades, 48 resultados previstos y 32 intents LLM; no se cambió la taxonomía, hipótesis, orden ni cálculo H1/H2. Ledger, checkpoints, autorización, control de presupuesto, interrupción y reanudación explícita se mantienen. El resultado completo contiene latencias, respuesta cruda, postcheck y decisiones. La evaluación ya distingue citas crudas, etiquetas finales, resultados no utilizables y denominadores.

**Decisión prospectiva que debe aprobarse antes del FREEZE:** el rechazo `evidence_check_incoherent` se trata como fallo ordinario del contrato de salida: se guarda, permanece en el denominador y no se reintenta. No detiene por sí solo la campaña. Un timeout, desconexión con circuito bloqueado, pérdida de memoria o respuesta no terminal sigue siendo un stop crítico. No se ha aplicado esta decisión a ningún resultado histórico ni ejecutado una campaña nueva.

Los planes/candidatos antiguos no representan el perfil nuevo. Su control de hashes debe rechazarlos tras estas modificaciones. No se refrescaron, reescribieron ni sellaron. Una preparación prospectiva autorizada debe preservar referencias y documentar el perfil nuevo y sus fuentes antes de solicitar aprobación. No ejecutar `prepare`, `refresh-candidate`, `seal` o `run` durante la verificación local.

## Linux/EC2: soporte y preflight pendiente

**Actualización posterior al diagnóstico AWS 0:** ver
[compatibilidad EC2 y política de admisión aprobada](ec2_linux_compatibility.md).
El recolector v2 verifica la raíz cgroup, consulta las ramas de aplicación y
Ollama y tolera smaps denegado conservando RSS como una métrica distinta.
La aprobación expresa posterior activa localmente `linux-resident-mode-aware-v1`:
modo 0 exige toda la RAM/cgroup y usa commit como diagnóstico; modo 2 exige
además margen de commit; modo 1 se rechaza. La misma decisión se utiliza en
estado, adaptador, monitor y preflight. Windows mantiene sus criterios anteriores.

La contabilidad Linux de solo lectura usa `/proc/meminfo`, los grupos del backend,
Ollama y descendientes y sus ancestros. Se toma el mínimo de RAM disponible y
márgenes finitos, sin sumar consumos superpuestos. No se utiliza swap como RAM,
no se reducen reservas ni parámetros y no se cambia overcommit ni el kernel.
Cada admisión/rechazo conserva versión, métricas, checks y motivos; no garantiza
ausencia de OOM ni autoriza por sí misma un despacho.

La ruta prospectiva obtiene RSS desde status y conserva privada/PSS solo si
smaps permite medirlas. Smaps denegado no impide observar RSS; ninguna de estas
métricas se interpreta como otra. cgroup v1, membresías no resolubles, falta de
RSS crítico, datos ambiguos o incompletos fallan de manera segura. El recolector
histórico Windows permanece intacto. Los registros de política también validan
que las observaciones derivadas y las jerarquías sean consistentes.

Las pruebas de portabilidad usaron archivos Linux sintéticos en Windows. No equivalen a ejecutar el sistema en Linux ni prueban la instalación EC2. El lock utiliza fcntl en Linux y msvcrt en Windows; ambos requieren verificación operativa en la infraestructura real.

Solicitar a Karol, sin pedir credenciales en esta etapa:

- Distribución, versión de Python, vCPU/RAM, almacenamiento libre y ubicación del repositorio.
- Versión de Ollama, modelo instalado, digest completo, contexto efectivo y confirmación CPU.
- Configuración de cgroups, acceso a proc/smaps, política de commit/overcommit y swap, margen disponible en frío y caliente.
- Usuario/ruta de trabajo y mecanismo de acceso aprobado para la siguiente etapa, sin compartir secretos en el repositorio.
- Paquete R7 original: entradas, requests/mensajes y respuestas de las 58 llamadas, política original, parámetros, versiones y hashes.

En Linux los comandos respaldados del servicio usan el entorno local correspondiente, por ejemplo:

```sh
export PSI_LLM_PROFILE=qwen3coder-v2
export PYTHONPATH="$PWD/backend:$PWD"
.venv/bin/python -m pip check
.venv/bin/python -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

En la siguiente etapa comprobar por loopback health/capabilities/provider status sin generar: identidad, memoria/commit/cgroups, proceso Ollama, contexto, CPU, disco, no residentes al inicio, ausencia de circuito bloqueado y exclusividad. No limpiar un circuito sin comprobar que el servidor quedó inactivo y registrar una recuperación autorizada. Comprobar permisos de escritura/checkpoints y locks sin usar muestras reservadas. La primera inferencia real necesita autorización separada.

## Antes del FREEZE

No se generó un FREEZE ni candidato definitivo. El equipo deberá revisar y registrar:

1. Commit exacto revisado y árbol limpio; dependencias y versiones Python, Node, Ollama y sistema operativo.
2. Modelo/digest, CPU y todos los parámetros efectivos; contexto, 2048 tokens de salida y 300 s sin reintentos automáticos.
3. Bytes de política y hash del texto normalizado enviado, esquema canónico y hashes de requests/contextos.
4. Estrategia, sanitizador, verificador y sus dependencias léxicas/estructurales; context builder, orquestador, adaptador, 1A/1B, fuentes del controlador y módulos nuevos de perfil/recursos.
5. Memoria host/cgroup, commit, procesos, permisos, disco, paths de resultados y checkpoints; infraestructura real del preflight.
6. Referencias y dataset autorizados por sus identidades, revisados por responsables sin usarlos para depurar; orden/counterbalance y presupuesto 32.
7. Reglas de fallo, denominadores, indeterminados, exclusiones, ausencia de reintentos, reanudación y stop crítico; aprobación explícita del manejo del rechazo del postcheck.
8. Métricas H1/H2 y su interpretación sin cambiarlas por resultados observados. Distinguir cita literal, soporte estructural limitado, soporte semántico y adjudicación humana.
9. Trazabilidad de raw, etiquetas originales/finales, decisiones, advertencias, latencias y evidencia; revisión humana y aprobación vinculadas al nuevo candidato.

El CLI existente ofrece, **solo después** de preparar/verificar/aprobar el nuevo candidato y FREEZE y disponer de autorización vinculada:

```sh
PYTHONPATH="$PWD/backend:$PWD" .venv/bin/python -B -m experiments.phase4 run --authorization /ruta/authorization.json
```

Ese comando existe; no se ejecutó y no debe usarse contra el candidato histórico ni como smoke test. `--resume` requiere autorización adicional ligada al ledger y no recupera un stop crítico automáticamente.

No se afirma cumplimiento del gate, calidad independiente ni F1 0,87 de la versión corregida. La latencia p95 CPU reportada de aproximadamente 320 s supera tanto el objetivo de 240 s como el timeout individual de 300 s; el timeout se conserva y los fallos deben contabilizarse honestamente.
