# Gemma v2 — preparación técnica de ejecución

**Controlador implementado; 1038 pruebas backend aprobadas, incluidas 39 nuevas.
Cero inferencias reales nuevas. Ejecución todavía NO autorizada.**

Se conserva el [protocolo v2.0](gemma4_local_development_v2.md) y su FREEZE SHA-256
`f27f87d077856ac4a03966f7b9ddcfa266aa929cbbd01e327a88eff08e82e745`.
No se editaron sus artefactos ni los históricos v1.

## 1. Controlador y persistencia

`experiments/gemma4_v2/` reutiliza Gemma4Adapter, AnalysisService, contratos y
validadores de procedencia, monitor y gate persistente existentes. No modifica
proveedores, prompts ni motores 1A/1B. Separa protocolo/autorización, ejecución,
evaluación y CLI; el directorio de ejecución es fijo, sin opción CLI para abrir
otros doce intentos en una carpeta nueva.

El lock OS de campaña y el gate de inferencia protegen las doce intenciones
secuenciales. Cada una tiene UUID, campaña, caso, orden y hash, persistidos con fsync
antes de HTTP. Cada resultado conserva el run_id del pipeline, petición, respuesta
cruda, bytes de transporte, errores, tokens, tiempos y muestras de memoria/procesos.
Resultados y checkpoints se crean exclusivamente, sin sobrescritura.

Antes de cada despacho se revalidan congelado, binding, autorización y payload.
Se preserva incluso la representación numérica original (`0` frente a `0.0`);
no se normaliza el congelado para adaptarlo al controlador. B/C solo difieren en
1A. No se envían 1B, referencias privadas ni respuestas previas al modelo.
La igualdad se verifica en las opciones enviadas; Ollama no devuelve cada ajuste
interno del muestreador. Digest, contexto, CPU, ausencia de pensamiento y cuentas
de tokens sí se comprueban cuando la API los informa.

Una reserva huérfana es un intento consumido de desenlace incierto y **no se
repite**. STOP y circuito interrumpido no se borran automáticamente. Un reinicio
entre llamadas completas requiere `--resume` y autorización nueva ligada al ledger;
un STOP operativo no se reabre con ese flag. Resultados ajenos a v2 se rechazan por
identidad, ledger/checkpoint y fecha anterior al inicio de la campaña.

## 2. Aplicación de ≥9/11 y aclaración previa

**Siempre se requieren al menos nueve conjuntos exactos entre los once casos
determinables.** V2-09 se excluye de exactitud y etiquetas TP/FP/FN/TN, y tiene su
control propio de abstención, riesgo e incertidumbre.

| Situación | Usabilidad | Exactitud |
|---|---|---|
| Las doce salidas son utilizables | 12/12 | Once conjuntos evaluables; mínimo 9/11 y máximo 11/11 |
| Una salida determinable es inutilizable | Puede quedar 11/12 | Denominador once; esa salida no es exacta ni un negativo verdadero |
| Solo V2-09 es inutilizable | Puede quedar 11/12 | Los once conjuntos pueden acertar; aun así falla el control propio de V2-09 |
| Lote incompleto | Cobertura parcial | Sin pase completo; progreso sobre el plan y métricas parciales identificadas |

No se convierte en 9/12, 10/12 ni en un porcentaje sobre solo salidas válidas.
Usabilidad, exactitud, P/R/F1 y anclas son requisitos conjuntos.

La [aclaración prospectiva v2.0-a1](../artifacts/gemma4_v2_execution_preparation/gate_clarification_v2.0-a1.json)
no altera umbrales. Explicita para aprobación previa la distinción entre:

- **Parada inmediata:** fallos críticos de seguridad/integridad/operación.
- **Continuación segura:** FP/FN ordinarios, rechazo del JSON interno/esquema/cita
  y truncamiento terminal, sin reparación ni reintento, incluso si el pase ya no
  fuera posible.
- **Invención semántica en texto inerte:** se conserva para la revisión humana y
  el gate de cero invenciones críticas; no se toma como ejecución real. El runner
  nunca obedece instrucciones generadas ni habilita herramientas.

El truncamiento solo permite continuar con `done=true`, `done_reason=length`,
modelo/contexto/CPU correctos, ausencia de herramientas/pensamiento inesperado,
tokens válidos dentro de límites y recursos/circuito seguros. Timeout, falta de
fin, tool_calls, cambio de modelo/hash o fallo del monitor son paradas. No se ha
observado ninguna respuesta v2 real para definir esta aclaración.

## 3. Evaluación y aprobación de referencias

El evaluador calcula exactitud fija sobre once, micro P/R/F1, métricas secundarias
sobre utilizables, tabla B01–B07, macro descriptivo con soporte positivo, citas
incluidas las de informes rechazados, contrastes B/C y gate. La omisión por salida
inválida se identifica como FN de cobertura del sistema; los casos no intentados
y V2-09 no se convierten en errores semánticos del modelo. Denominadores cero
quedan en null y no producen un pase.

La [tabla completa de referencias](gemma4_v2_reference_approval.md) contiene textos
exactos, justificaciones, exclusiones, recuperaciones y parejas. **Las doce siguen
como propuestas asistidas por IA**, incluida V2-01 tras la aclaración de procedencia.
La aceptación de la estructura del protocolo no equivale a adjudicar etiquetas.

Las revisiones futuras se añaden en `execution/reviews/`, sin modificar las fichas
congeladas. Deben declarar persona, fecha, tipo `human_personal`, confirmación,
campaña/caso y hash del resultado, y clasificar soporte, invenciones, contradicciones,
riesgo/incertidumbre e inyección. Una ficha sin confirmación, con hash viejo o con
fecha anterior al resultado no permite pase. No se presume independencia humana.

## 4. Recursos para el momento de ejecución

No se midió ni se supone libre ahora la RAM anterior. El preflight bajo gate exige:

- **15.135.148.032 bytes** disponibles simultáneamente en RAM física y compromiso
  para frío: **14,10 GiB redondeados**, valor exacto del congelado. El margen de
  2 GiB ya está incluido; no se suma dos veces.
- Inicio sin modelos residentes, sin otras inferencias y con declaración veraz de
  sesión exclusiva. El lock excluye clientes de la aplicación; no puede impedir
  por sí mismo solicitudes futuras de otras aplicaciones.
- Digest previsto, Q4_K_M, completion, think=false, contexto compatible y runtime
  ≥0.30.9; sin descarga, actualización o fallback. Metadata limitada a 5 s y chat a
  deadline absoluto de 300 s, cero reintentos.
- Disco libre ≥2 GiB; registrar compromiso total/usado y árbol Ollama con llama-server.
  Fallo de inventario o contadores impide afirmar supervisión completa.
- En residencia CPU/contexto 8192 correctos, antes de cada llamada posterior:
  ≥3 GiB libres en RAM y compromiso. Si cambia/no hay residencia, vuelve la reserva
  fría. Durante inferencia: suelo de 2 GiB, muestreo aproximadamente cada segundo,
  cancelación y circuito persistente ante infracción o fallo del colector.

## 5. Autorización y comandos

El [binding](../artifacts/gemma4_v2_execution_preparation/runner_binding.json) liga
código, pruebas y documentos al congelado sin modificarlo. La
[plantilla de autorización](../artifacts/gemma4_v2_execution_preparation/execution_authorization.template.json)
está deshabilitada y no contiene declaración del responsable ni aceptación de
referencias. **No existe autorización operativa ni ledger v2.** Solo tras un mensaje
explícito se deberá crear un registro nuevo ligado a esos hashes, con aceptación
de referencias/aclaración, presupuesto doce y exclusividad comprobada.

Verificación sin inferencia, ya realizada:

```powershell
$env:PYTHONPATH = 'backend;.'
.venv/Scripts/python.exe -m experiments.gemma4_v2 verify
```

**Comando preparado, NO ejecutado:**

```powershell
$env:PYTHONPATH = 'backend;.'
.venv/Scripts/python.exe -m experiments.gemma4_v2 run --authorization artifacts/gemma4_development_v2/execution_authorization.json --exclusive-session-attested
```

El archivo indicado no existe todavía. La exclusividad solo deberá declararse
cuando se haya comprobado realmente. El controlador valida autorización antes
de construir un cliente de modelo o reservar presupuesto. No hay flag para omitir
autorización o reintentar. La aceptación de v2 no resuelve implícitamente v1.

Con resultados y revisiones personales, `evaluate` escribe un informe nuevo con
UUID sin reabrir ejecución. Un pase solo sería candidato de desarrollo para
selección independiente autorizada aparte.

## 6. Pruebas e integridad

**1038 pruebas backend aprobadas, cero fallos/errores/omitidas; 67,08 s**, incluidas
las **39 pruebas nuevas**. [JUnit definitivo](../artifacts/gemma4_v2_execution_preparation/backend_regressions.xml).
Se simularon continuación tras FP/rechazos, paradas críticas y de recursos, hashes,
presupuesto/reinicios, citas originales/recuperadas, métricas y 9/11 con doce salidas
utilizables, rechazo de v1 y aislamiento de selección. Los tests nuevos prohíben
sockets/subprocesos y usan presupuestos y revisores ficticios solo en carpetas temporales.

No se presentan esas respuestas o revisores como resultados de Gemma o decisiones
humanas reales. No se cambiaron tests históricos ni se instalaron dependencias.
El [recibo final](../artifacts/gemma4_v2_execution_preparation/delivery_verification.json)
comprueba históricos, congelado, Gemini 5/12 e índice/HEAD. Cero inferencias nuevas,
sin muestras ejecutadas, selección independiente o Fase 4. La rama sigue en develop.
