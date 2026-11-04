# Cierre de Fase 3 — PowerShell Insight AI

**Fecha: 2026-11-02, America/Bogota.** MVP web local implementado con FastAPI y React.
La Fase 3 queda **completada técnicamente en implementación y pruebas automatizadas**, con
una limitación explícita: no hubo revisión visual en navegador porque el host de acceso no
estuvo disponible. No se afirma una comprobación visual/responsive ni capturas inexistentes.
El modelo continúa provisional; la Fase 4 no se inició.

## A. Pendientes antes de Fase 4

Se registraron antes de escribir el backend/frontend, en [phase4_pending.md](phase4_pending.md)
y el roadmap: cierre metodológico del piloto interrumpido, selección definitiva del modelo,
resolución de memoria para campañas largas, evaluación independiente A/B/C, adjudicación
semántica humana, contraste de H1/H2 y congelación definitiva de datos/criterios/prompt/opciones/entorno.

El piloto v2 conserva su estado **PENDIENTE / INCONCLUSO**, 58 intentos históricos y 68 llamadas
de selección pendientes. Esta entrega no modifica los criterios ni reabre selección, ni
convierte funcionamiento de la aplicación en validación de Qwen3.5. DEV-03 sigue limitándose
a permitir desarrollo con un candidato provisional.

## B. Backend

FastAPI 0.162.0, Uvicorn 0.54.0, Starlette 1.10.0 y Python 3.13.3. Se añadieron dependencias
web fijadas en `backend/requirements-app.txt`, conservando intacto el archivo del piloto.
`pip check` no encontró requisitos rotos.

| Endpoint | Función |
|---|---|
| `GET /api/health` | API y actividad, independiente del estado de Ollama |
| `GET /api/metadata` | Versión 0.3.0, esquemas y estado metodológico |
| `GET /api/capabilities` | A/B/C/ABC, límites, modelo, digest y opciones |
| `GET /api/ollama/status` | Consulta de servicio, instalación, recursos y circuito, sin inferencia |
| `POST /api/analyze/{A,B,C}` | Ejecutar un pipeline existente |
| `POST /api/compare` | Tres resultados independientes sobre el mismo texto |
| `GET /openapi.json` | Contrato HTTP reutilizable |

`AnalysisRequest` acepta exclusivamente un campo `script` de tipo string. No permite enviar
modelo, etiquetas, parámetros privados o historial. Reutiliza `PipelineResult`/`ComparisonResult`
de Fase 2 sin reescribir ni modificar motores, prompts, validación o servicios históricos.
El estado de ejecución pertenece al contrato; un rechazo del modelo no se convierte en hallazgo.

El trabajo síncrono corre en threadpool fuera del event loop. La API admite hasta dos A y una
petición B/C/ABC por proceso, más una consulta de estado; exceso devuelve 409, sin cola de
inferencias ilimitada. La exclusión OS y el circuito de Fase 2 continúan protegiendo la inferencia
entre instancias. A y health siguen respondiendo mientras se bloquea una llamada LLM simulada.

Se limita el cuerpo antes de parsear y el texto después en bytes UTF-8; se rechazan tipos,
campos extra y entradas vacías. Se verifican origen y host locales, JSON obligatorio en POST,
CORS explícito, respuestas sin caché y headers de protección. La app no persiste muestras,
no ofrece ejecución, descargas de modelos o modificación de protecciones. El build se sirve
solo desde `frontend/dist`; fuentes Python/datasets y traversal no son accesibles por ese montaje.

El adaptador web extiende el transporte existente: lecturas auxiliares limitadas a 3 s y
chat con el timeout configurado, máximo 300 s. No altera modelo, prompt ni política B/C.
No se incluyen Swagger/ReDoc remotos; la documentación es local y el esquema OpenAPI está disponible.

## C. Frontend

React 19.3.1 + Vite 8.3.5 + TypeScript 7.0.2, con dependencias exactas y `package-lock.json`.
Los componentes separan editor, estado del sistema, resultados, primitivas y guía contextual;
el cliente HTTP y contratos de vistas están en módulos propios.

Funcionalidades implementadas:

- Analysis Studio con pegado, lectura de archivo `.ps1/.txt` UTF-8, contador de bytes, ejemplo
  sintético, limpieza y ejecución explícita con botón o Ctrl+Enter.
- Selección A/B/C/ABC; no se analiza automáticamente al cargar el ejemplo, archivo o página.
- Estados vacíos, loading sin porcentaje inventado, errores de conexión, respuestas rechazadas,
  parciales, indisponibilidad y resultados anteriores marcados si el texto cambió.
- Hallazgos, confianza declarada del modelo, riesgo atribuido, incertidumbre, técnicas rotuladas
  por autor, evidencias, recuperación determinista, reconstrucción LLM no verificada y diagnóstico.
- Comparación de tres tarjetas con estados/autores/etiquetas, diferencias visuales y detalles
  independientes; sin ganador, precisión, F1 o score de calidad.
- Ubicación de raíz en el editor, con conversión de coordenadas Python a UTF-16 del textarea y
  normalización CRLF sin cambiar la entrada que se analizó.
- Exportación explícita del JSON completo; no hay historial automático ni almacenamiento local
  de muestras/resultados. Solo persiste el tema bajo `psi-theme`.
- Estado API/Ollama/modelo/digest/memoria/circuito y consulta manual disponibles desde el
  encabezado también en móvil; guía de modos, taxonomía y pendientes científicos.

Los datos se renderizan como texto de React. No se usa `dangerouslySetInnerHTML`, ejecución
de código, Markdown activo o enlaces automáticos de URLs de muestras. El test de respuesta
adversaria conserva `<img ...>` como texto y comprueba que no aparece un elemento ejecutable.

## D. Diseño y UX

La investigación en Internet se hizo antes del frontend: dashboards SaaS/developer tools,
seguridad, split views, tabs y temas. Las fuentes y su aplicación están en
[phase3_design.md](phase3_design.md), con enlaces a los materiales públicos de Linear, Geist
y Snyk. No se clonaron marcas ni se importaron sus imágenes o métricas.

Identidad propia: azul tinta, superficies de pizarra, menta para acciones y estado operativo,
ámbar para provisionalidad/incertidumbre y rojo para rechazo. Temas claros/oscuros mediante
tokens; fuentes Inter y JetBrains Mono empaquetadas localmente. Editor/resultados en paneles,
jerarquía de resumen antes del detalle, whitespace, estados diseñados y layout adaptable.
No se añadió Tailwind o Monaco: CSS propio y editor textarea mantienen un MVP acotado.

Accesibilidad implementada: radios nativos, labels, foco visible, enlace de salto, tablist
con flechas/Home/End, diálogo nativo, estados además del color, `aria-busy`, regiones live y
preferencia de movimiento reducido. Se revisó numéricamente contraste de los tokens secundarios;
no se declara conformidad WCAG ni auditoría visual completa.

**Límite concreto:** `cua.getState` informó ausencia de host de navegador y pipe nativo;
el intento de abrir `http://127.0.0.1:8000` devolvió “The browser access host is unavailable”.
No se sustituyó por capturas fabricadas o por considerar JSDOM un motor visual. Queda revisión
manual de layout, scroll, temas y breakpoints en un navegador real, con procedimiento en la guía.

## E. Integración A/B/C

UI → `/api` → `AnalysisService` existente → resultado Pydantic → vista con autoría:

- A: 1A + 1B; no Ollama ni inferencia; no riesgo inferido a partir de ofuscación.
- B: original como única entrada de análisis del LLM; ninguna salida determinista adicional.
- C: original + recuperación permitida de 1A; nunca recibe etiquetas, decisiones o riesgos de 1B.
- Comparación: tres UUID/resultados, mismo hash original, B/C separados y sin conversación compartida.

La UI no concatena resultados para enviarlos al modelo. Tampoco usa A como oráculo para
corregir silenciosamente B/C. Las técnicas de 1A y las declaraciones LLM se muestran con
autoría distinta incluso si comparten código de técnica. Los errores conservan su causa y
no producen etiquetas aceptadas. Los límites/advertencias/indicadores de los motores son consultables.

Los controles de memoria, digest, contexto y truncamientos de Fase 2 permanecen intactos.
El ejemplo de UI es texto sintético nuevo; no procede de selección ni de evaluación final.

## F. Pruebas

| Comprobación final | Resultado | Evidencia |
|---|---|---|
| Backend completo | **876 aprobadas**, cero fallos/errores/omitidas; 17,62 s | [JUnit backend](../artifacts/phase3/backend_tests.xml) |
| Regresiones previas incluidas | **841 preservadas**; línea base también pasó antes de implementar API/UI | [Línea base](../artifacts/phase3/baseline_tests.xml) |
| Nuevas pruebas de API | **35 aprobadas**, incluidas en 876 | Endpoints, errores, payloads, origen/host/body, estado, concurrencia y contratos |
| Frontend | **24 aprobadas**, cero fallos/omitidas; 8,75 s | [JUnit frontend](../artifacts/phase3/frontend_tests.xml) |
| React + API HTTP real | **1 aprobada**, solo A; 1,56 s | [JUnit conexión](../artifacts/phase3/connected_tests.xml) |
| TypeScript + build Vite | Correctos; build final 359 ms tras typecheck | [Recibo final](../artifacts/phase3/final_verification.json) |
| Dependencias | `pip check` y `npm ls --depth=0` correctos | [Entorno](../artifacts/phase3/environment.json) |

Backend verifica serialización, A/B/C/ABC, mismo modelo/opciones y proyección de contextos,
errores estructurados, zero inference en health/status, tipos/campos extra, bytes UTF-8,
JSON inválido, aislamiento HTTP, respuesta parcial/rechazada/indisponible, admisión limitada,
A/health durante LLM lento simulado y archivos estáticos fuera del repositorio.

Frontend verifica vacío/loading/error, selección y duplicados, payload exacto, archivos UTF-8,
límites, no inferencia inicial, temas/persistencia, ayuda, estado móvil accesible desde header,
procedencia y técnicas por autor, diferencias sin métricas, incertidumbre, rechazo sin HTML,
tabs/teclado, evidencias/selección y coordenadas Unicode/CRLF. Las tres fixtures JSON propias
se revalidan con los contratos Pydantic desde la suite de backend.

Se corrigió un fallo del cliente que reconocía AbortError solo por `instanceof Error`, lo que
podía fallar entre realms. Las pruebas iniciales también corrigieron expectativas de nombres
accesibles y un cast de JSON de fixture; los resultados finales anteriores corresponden al
código entregado. No se modificaron pruebas históricas para hacerlas pasar.

Aviso no bloqueante conocido: Starlette 1.10 depreca su TestClient sobre el `httpx` 0.28.1
del entorno histórico y recomienda `httpx2`. Las pruebas pasan; no se reemplazó el transporte
histórico para silenciarlo. El aviso queda registrado, sin fallo de requisitos en `pip check`.

## G. Validación funcional

**Cero inferencias nuevas de Ollama en Fase 3.** No hizo falta repetir las seis llamadas de
Fase 2. Las pruebas B/C usan transporte/respuestas sintéticas, declaradas como tales.
Se realizaron consultas de estado locales de solo lectura, que no ejecutan chat ni cargan pesos.

La comprobación React/JSDOM contra el servidor FastAPI real carga el ejemplo, envía A, muestra
B05/Reconocimiento y recuperación `studio-local`, y abre la ayuda que conserva provisionalidad.
No es una prueba de renderizado visual en navegador ni de calidad del LLM.

También se verificaron por HTTP real el build en 8000, JS/CSS, health, metadata, capabilities,
OpenAPI, Vite en 5173 y su proxy. Un POST de A a través del proxy devolvió B05, fuente exacta,
trazas deterministas y `llm=null`, con cero llamadas de modelo. [Diez checks HTTP](../artifacts/phase3/http_smoke_final.json)
y [resultado A del proxy](../artifacts/phase3/dev_proxy_A.json).

Los servidores temporales de verificación se detienen al entregar. Los comandos de la
[guía local](phase3_local.md) permiten iniciarlos o usar un único servidor de demo.

## H. Limitaciones

| ID | Pendiente / límite real |
|---|---|
| P3-UI-01 | Revisión visual en navegador, mobile/tablet, scroll y foco nativo pendiente por host indisponible; CSS responsive implementado, sin certificación visual |
| P3-LLM-01 | Qwen3.5 mantiene defectos graves de calidad de Fase 2; citas literales y JSON correcto no los resuelven |
| P3-OPS-01 | Sin campaña larga ni nueva inferencia real; integración HTTP de B/C cubierta con simulación y servicio histórico real preservado |
| P3-TEST-01 | Aviso de deprecación TestClient/httpx en el nuevo Starlette; pruebas pasan y dependencias son coherentes |
| P3-SCOPE-01 | MVP solo loopback, sin autenticación multiusuario, historial, despliegue público o cancelación garantizada desde el navegador |
| P3-CORE-01 | Se mantienen subconjuntos, límites de contexto conservadores y abstenciones/FN conocidos de 1A/1B/2 |

No se ejecutaron muestras, sus URLs, PowerShell recuperado ni salidas LLM. No se cerraron
aplicaciones del usuario ni se cambiaron protecciones o ajustes globales. Solo se instalaron
dependencias del proyecto y se gestionaron los servidores de verificación propios.

## I. Estado real de Fase 3

**MVP técnico FastAPI + React completado**, integrado con A/B/C, probado automáticamente,
con instrucciones de ejecución y evidencia de conexión real. No hay defectos críticos de
software conocidos sin registrar. **La revisión visual real queda pendiente** por una
limitación del entorno, no se reporta como aprobada. Se conserva separada de la implementación
y de la aceptación científica pendiente del modelo.

## J. Preparación para Fase 4

Ya existen API, UI, contratos, parámetros trazables, exportación y comparación funcional.
Eso facilita inspección, demostración y consumo futuro por un evaluador separado. No aporta
familias nuevas congeladas, ground truth independiente, revisión humana, calidad validada,
memoria estable en campañas o evidencia de H1/H2. Esas obligaciones están en la lista previa
de siete pendientes, sin bloquear el desarrollo realizado ni iniciar evaluación final.

## K. Git y archivos

Rama **develop**, todo local y sin staging. No se ejecutaron `git add`, `commit`, `push`,
`merge`, `rebase`, `reset --hard` o `clean`. Índice e historial conservados, verificando el hash
de `.git/index` frente al inicio y el staging vacío. `git diff --check` pasó.

Modificados: `README.md`, `docs/architecture.md`, `docs/roadmap.md`, `.env.example`.
Nuevos: `backend/app/api/` (aplicación, contratos y transporte web), `backend/app/main.py`,
`backend/requirements-app.txt`, pruebas API; proyecto React completo bajo `frontend/` con
configuración/lock, componentes, hooks, cliente/tipos, estilos, favicon y pruebas/fixtures;
`docs/phase4_pending.md`, guía local, diseño y este cierre; evidencias bajo `artifacts/phase3/`.

No se editaron motores/contratos/prompts de Fase 2, pilotos, datos, congelaciones, umbrales,
resultados históricos ni pruebas previas. Se comparan sus hashes con el inventario tomado al
inicio; el [inventario de entrega](../artifacts/phase3/delivery_inventory.json) enumera cada
archivo nuevo/modificado y distingue dependencias/builds ignorados. El [recibo de integridad](../artifacts/phase3/final_verification.json)
conserva los controles, resultados y límites sin adjudicaciones científicas inventadas.
