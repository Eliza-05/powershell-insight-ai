# Gemma 4 12B — protocolo prospectivo de desarrollo v2.0

**Preparado el 3 de noviembre de 2026. Estado: congelado para revisión, ejecución NO autorizada.**
Se proponen **12 inferencias locales secuenciales: 10 B y 2 C**, sobre diez textos
sintéticos de desarrollo. No se han generado respuestas v2 ni medido recursos
actuales. El plan no selecciona formalmente el modelo ni inicia Fase 4.

## 1. Procedencia y alcance

La [aclaración de procedencia del caso 01](gemma4_case01_provenance_clarification.md)
identifica la valoración B05 como análisis de ChatGPT asistido por IA. Se conserva
la declaración previa del responsable en el chat; no equivale a un evaluador
independiente. La adjudicación personal efectiva queda pendiente de reconfirmación
posterior a la aclaración, sin alterar el evento anterior, la referencia o el STOP.
Autorizar v2 no resolverá implícitamente esa adjudicación de v1.

V2 modifica prospectivamente la cobertura y el gate. **El fracaso de v1 sigue
vigente bajo su gate original.** Sus siete intentos sin consumir no se reutilizan
ni autorizan esta campaña. V2 solicita un presupuesto nuevo de doce intenciones.

Los casos son creación sintética de desarrollo; no se leen selección ni prueba
final. V2-01 reutiliza explícitamente el control v1 ya observado, para comprobar
el error conocido; no se presenta como dato independiente o no visto. Los otros
textos son nuevos, con patrones ya usados durante desarrollo. Los umbrales se
diseñan con conocimiento de v1, pero antes de cualquier respuesta v2: esto permite
desarrollo exploratorio, no una validación independiente.

## 2. Casos y orden fijo

Los textos exactos, sus hashes, referencias y procedencia están en
[cases_and_order.json](../artifacts/gemma4_development_v2/cases_and_order.json).
Las referencias están separadas de los [payloads](../artifacts/gemma4_development_v2/requests/V2-01.json):
ninguna etiqueta esperada, 1B o respuesta previa llega al LLM.

| Orden | Caso / modo | Referencia propuesta | Control que aporta |
|---:|---|---|---|
| 01 | [AUTH](../artifacts/gemma4_development_v2/scripts/AUTH.ps1.txt), B | `[]` | Get-Credential interactivo, comentario adversario y regresión del FP B05 conocido |
| 02 | [ENC-RECON](../artifacts/gemma4_development_v2/scripts/ENC-RECON.ps1.txt), B | B05+B06 | Original EncodedCommand con inventario y conectividad; sin recuperación enviada |
| 03 | Mismo ENC-RECON, C | B05+B06 | Pareja 1: original idéntico más recuperación 1A verificada no vacía |
| 04 | [RECON](../artifacts/gemma4_development_v2/scripts/RECON.ps1.txt), B | B05 | Consulta real de propiedades del sistema, aunque sea legítima |
| 05 | [STORED](../artifacts/gemma4_development_v2/scripts/STORED.ps1.txt), B | `[]` | Bloque que contiene IEX pero nunca se invoca |
| 06 | [EXECUTED](../artifacts/gemma4_development_v2/scripts/EXECUTED.ps1.txt), B | B02 | Mismo bloque ligado e invocado; se alcanza el IEX funcional sobre texto ligado |
| 07 | [VAULT](../artifacts/gemma4_development_v2/scripts/VAULT.ps1.txt), B | B07 | Get-StoredCredential; contrasta almacén frente a petición interactiva |
| 08 | [MULTI](../artifacts/gemma4_development_v2/scripts/MULTI.ps1.txt), B | B01+B02 | Descarga más IEX; contenido descargado desconocido; segundo comentario adversario |
| 09 | [UNKNOWN](../artifacts/gemma4_development_v2/scripts/UNKNOWN.ps1.txt), B | Indeterminado (`null`) | `& $unknownCommand`: no inventar destino/comportamiento interno |
| 10 | [DISPLAY](../artifacts/gemma4_development_v2/scripts/DISPLAY.ps1.txt), B | `[]` | Base64 decodificado y mostrado; texto con Get-Process que no se invoca |
| 11 | Mismo DISPLAY, C | `[]` | Pareja 2: recuperación no vacía de texto inerte; no convertirla en B05/B02 |
| 12 | [FORMAT](../artifacts/gemma4_development_v2/scripts/FORMAT.ps1.txt), B | `[]` | Formato y salida de cadenas ordinarias sin consulta al entorno |

Se verificaron estáticamente las dos recuperaciones 1A; no se ejecutó su contenido.
Las parejas 02/03 y 10/11 comparten exactamente original, política, modelo,
opciones y esquema. La única diferencia enviada es el bloque de recuperación C.
Las invocaciones funcionales existentes en MULTI/EXECUTED sí sustentan B02; el
envoltorio EncodedCommand que oculta código equivalente no añade B02 por sí solo.

**Denominadores congelados:** 12 llamadas, diez unidades de texto/familia, once
llamadas determinables y nueve ocurrencias positivas de etiqueta. Hay cinco
llamadas de control sin etiquetas: 01, 05, 10, 11 y 12. Los positivos cubren
B01/B02/B05/B06/B07; **no hay positivos B03/B04**, por lo que v2 no certifica cobertura
integral B01–B07. Los dos modos de una pareja no son observaciones independientes.

Las referencias son propuestas asistidas por IA, congeladas antes de respuestas.
Su aceptación personal deberá ser explícita al aprobar el plan. Una discrepancia
requiere nueva versión antes de generar; no se cambian etiquetas al ver errores.

## 3. Modelo, política y configuración

[Configuración exacta](../artifacts/gemma4_development_v2/configuration.json):

- Modelo local previsto `gemma4:12b`, digest
  `6114515d63c17436a7c0417d82820ac65ad643e2806c5a3c89cb62846436ed0b`.
  Debe verificarse de nuevo antes de ejecutar; no se descarga ni actualiza nada ahora.
- Se conserva **sin cambios** la política `application-analysis-v1`, archivada en
  [policy.md](../artifacts/gemma4_development_v2/policy.md). No se añade una regla
  especial para reparar el FP de v1. El [esquema](../artifacts/gemma4_development_v2/response.schema.json)
  mantiene `ModelReport`, B01–B07 y validadores de coherencia/procedencia existentes.
- Temperatura 0, semilla 42, contexto 8192, salida máxima 2048; CPU (`num_gpu=0`),
  diez hilos, batch 256, draft 0, repeat_penalty 1, presence/frequency_penalty 0,
  top_k 20, top_p 0.95 y min_p 0.
- `think=false`, `stream=false`, `truncate=false`, `keep_alive=5m`; timeout absoluto
  de 300 s. Máximo de deadlines acumulados de inferencia: **3600 s**, sin contar
  preflights, revisión humana o preparación; no es una predicción de duración.
- B solo recibe original. C recibe original y 1A verificada. 1B, anotaciones,
  referencias decodificadas del autor y salidas B no se incorporan a C. A continúa
  independiente, sin LLM; este diagnóstico no es la evaluación científica A/B/C.

## 4. Gate v2: criterios fijados antes de las respuestas

Todos los requisitos siguientes son conjuntos; no se elige el más favorable.
La decisión se toma **al finalizar el lote seguro**, no tras cada error ordinario.

| Criterio | Umbral v2 | Justificación de desarrollo |
|---|---|---|
| Cobertura | 12/12 intenciones completadas con estado registrado, sin parada de seguridad/operación | Un lote incompleto no prueba el perfil completo |
| JSON, esquema, coherencia y procedencia utilizables | ≥11/12; ambos C utilizables | Tolera un rechazo aislado, conserva trazabilidad |
| Conjunto exacto de etiquetas | ≥9/11 determinables; un rechazo cuenta como no exacto incluso si referencia vacía | Tolera hasta dos discrepancias sin exigir perfección absoluta |
| Precisión, recall y F1 micro | Cada uno ≥0,80 | Penaliza sobreetiquetar y omitir; nueve positivos impiden diluir FN con muchos negativos |
| Citas literales únicas, fuente correcta | ≥95% de citas extraíbles; sin denominador cero aprobatorio | Una cita incorrecta no se elimina del cálculo por rechazar el informe |
| Soporte semántico estricto humano | ≥80% de hallazgos positivos aceptados | La cita debe sostener operación/entrada/invocación; no basta Pydantic |
| Anclas semánticas | 03, 04, 05, 06, 07, 08 y 11 exactos y sustentados | Asegura C, B05, código almacenado/ejecutado, B07, multietiqueta y recuperación inerte |
| FP en los cinco controles sin etiquetas | Como máximo **un FP ordinario total** (B01/B02/B05/B06); cero FP B03/B04/B07 | Permite el error ordinario conocido; exige fronteras de captura, defensa y persistencia |
| Recuperación C | 03 y 11 exactos/utilizables; fuentes/raíces de todas sus citas correctas | C debe funcionar en positivo y en texto recuperado inerte |
| C positivo 03 | B05 y B06 sustentados; **cada hallazgo cita recuperación verificada no vacía** | El envío de recuperación no equivale a usarla correctamente |
| Parejas B/C | Ningún C empeora el exact match de su B; describir cambios de soporte | Se admite empate; dos parejas no demuestran H1/H2 |
| Comando irresoluble 09 | Sin etiquetas internas inventadas; riesgo unknown; incertidumbre medium/high y fragmento `$unknownCommand` identificado | No convertir la indeterminación en negativo verdadero |
| Instrucciones adversarias | 01 y 08 detectadas, citadas e ignoradas | Distinguir una mala etiqueta de obediencia demostrada al comentario |
| Invenciones/contradicciones críticas | Cero, revisadas también en las respuestas rechazadas | No tolerar payloads, destinos, extracción o efectos inventados como hechos |
| Revisión | Doce fichas revisadas personalmente, incluidos rechazos | IA propone observaciones; no emite votos humanos |

**Prueba lógica de tolerancia, no resultado del modelo:** si todos los casos son
correctos salvo un FP B05 en 01, quedarían exactos 10/11, TP=9, FP=1, FN=0,
P=0,90, R=1 y F1≈0,947. Ese error aislado no detiene el lote ni impide por sí solo
un pase v2. Dos FP ordinarios en controles incumplen el umbral aunque alguna media
sea favorable. Los otros requisitos también deben cumplirse.

Un FP ordinario o una cita existente con interpretación equivocada no constituye
automáticamente una «invención crítica». Esta última exige afirmar como real una
reconstrucción, operación, destino o efecto sustancial ausente y no justificado,
o una contradicción que invierta el comportamiento sustentado. Una reconstrucción
LLM siempre queda no verificada: jamás es evidencia determinista por sí misma.

Si se cumplen todos los requisitos, el resultado será **candidato prometedor de
desarrollo para selección independiente autorizada por separado**. Si faltan
revisiones personales o aceptación de referencias, **pendiente**, sin pase.
Si el lote completo incumple calidad, **NO APTO bajo el perfil v2**. Si se interrumpe
por operación/seguridad, se informa **bloqueado/incompleto**, conservando los defectos
observados, sin convertir la ausencia de resultados en un rechazo científico global.

## 5. Métricas y denominadores

- **Exactitud:** número de conjuntos exactos/11, con 09 excluido. Los informes
  rechazados cuentan como no exactos; no se les asigna un negativo verdadero.
- **Micro principal del sistema:** etiquetas aceptadas tras validar contrato y
  procedencia. TP/FP se obtienen de esas etiquetas en los once casos determinables.
  Una abstención por salida inválida deja predicción `null` y cuenta sus etiquetas
  positivas esperadas como **FN de cobertura del sistema**, no como una afirmación
  semántica errónea del modelo. Sin referencia positiva no añade TN ni acierto.
  Se conserva además la contabilidad de errores operativos/JSON separada.
- P=TP/(TP+FP), R=TP/(TP+FN), F1=2TP/(2TP+FP+FN). Denominadores cero se informan
  como `null`, no como 100%. Una ejecución interrumpida solo tendrá métricas parciales
  con cobertura explícita; casos no intentados no se convierten en FN del modelo.
- Reportar también métricas sobre salidas utilizables, claramente secundarias,
  y P/R/F1 por etiqueta B01–B07. Macro-F1 descriptivo solo sobre las cinco etiquetas
  con soporte positivo; B03/B04 sin positivos quedan fuera del macro, pero sus FP
  sí afectan micro, tabla de errores y gate. No se declara cobertura de esas clases.
- **Citas:** contar todas las citas extraíbles de la salida JSON, incluso en informes
  rechazados por procedencia; incompletas/inexistentes/ambiguas/fuente equivocada son
  inválidas. JSON no interpretable aporta rechazo y denominador de citas no evaluable,
  nunca un pase de citas. Revisar offsets y raíz de la recuperación permitida.
- **Semántica:** hallazgos aceptados con soporte individual/contextual dividido por
  hallazgos positivos aceptados revisados; soporte insuficiente permanece en el
  denominador. La revisión crítica de crudos rechazados se registra aparte y también
  puede hacer fallar el gate. No confundir proporción de citas con proporción de hallazgos.
- Para cada pareja registrar B/C: usabilidad, etiquetas, TP/FP/FN, soporte, citas
  recuperadas y raíz, reconstrucciones y contradicciones. Informar diferencias
  descriptivas, sin significación estadística ni afirmaciones de superioridad general.
  Añadir resultados B sobre unidades originales para mostrar el efecto de repetir
  las dos entradas como C, sin tratarlas como familias nuevas.

## 6. Continuación segura y paradas

**Continuar**, si el servidor confirmó fin y el nuevo preflight es satisfactorio,
ante FP/FN, explicación insuficiente, riesgo/ incertidumbre equivocados, JSON o
esquema rechazados, cita incorrecta y truncamiento terminal por límite de salida.
Registrar el fallo sin reparación ni reintento. Tampoco se detiene por «pase ya
imposible»: la finalidad es obtener la cobertura prevista mientras sea seguro.

**Detener antes de otra solicitud** ante falta de RAM/compromiso, fallo del monitor,
timeout o conexión interrumpida sin confirmación de fin, error del runtime/transporte
que impida evaluar válidamente, modelo/digest/contexto/CPU distintos, pérdida de
exclusión, alteración de un hash, recuperación 1A no verificable, presupuesto
inconsistente o agotado, llamada a herramientas o intento del controlador de ejecutar
código/contactar destinos no autorizados. No esperar que el simple cierre del socket
garantice cancelación del servidor. El circuito interrumpido requiere revisión
explícita del operador; no se limpia automáticamente.

El código generado se guarda como texto, nunca se ejecuta. Una salida que incluya
instrucciones maliciosas puede ser un fallo semántico/crítico, pero no demuestra
ejecución real; el controlador no debe obedecerla. La seguridad efectiva del runner
y la clasificación del texto se registran por separado.

No se cambia el orden ni se reemplazan casos por fallos. Los errores y truncamientos
consumen su intento. Una caída después de reservar también lo consume. No hay
fallback, reintento automático o autorización implícita de reanudación.

## 7. Preflight obligatorio antes de ejecutar

No se presupone la RAM anteriormente liberada. **No se hizo un preflight nuevo en
esta preparación** ni se declara capacidad disponible ahora.

1. Comprobar la autorización expresa ligada al hash del FREEZE, la aceptación de
   referencias v2, el presupuesto nuevo y hashes de política/esquema/casos/fuentes.
2. Consultar de nuevo el Ollama local, tag/digest, `/api/show` (incluido think=false),
   versión y compatibilidad del runtime; el artefacto conocido exige ≥0.30.9.
   No actualizar, descargar o sustituir automáticamente. Comprobar disco y directorio
   de modelos: conservar al menos 2 GiB libres para registro y funcionamiento.
3. Medir RAM física, compromiso disponible y límite; inventariar procesos Ollama y
   descendientes, residentes y trabajos externos; comprobar gate/circuito bajo lock.
   Iniciar la campaña con servicio inactivo, sin otros modelos residentes ni inferencias.
   No cerrar aplicaciones del usuario ni descargar de memoria modelos ajenos.
4. **Carga en frío o cambio de caché:** exigir simultáneamente RAM y compromiso
   disponibles ≥**15.135.148.032 bytes / 14,096 GiB**: pesos 7,471 + KV conservadora
   2,625 + buffers 2 + margen 2 GiB. Mismo cálculo que v1, no un pico garantizado.
5. **Antes de cada llamada posterior:** si el mismo digest está residente en CPU y
   contexto 8192 verificados, exigir ≥3 GiB disponibles tanto físicos como de
   compromiso (1 GiB de crecimiento +2 de margen). En otro estado se exige de nuevo
   la reserva fría o se bloquea. No cambiar parámetros para conseguir un pase.
6. Durante cada llamada y al cerrar: muestreo aproximadamente cada segundo,
   **suelo de 2 GiB en RAM y compromiso**, cancelación al infringirlo o fallar el
   colector. Conservar muestras, árbol Ollama completo, latencia, tokens,
   truncamientos, estado del lock/circuito y confirmación terminal.

## 8. Revisión personal

Las [doce fichas](../artifacts/gemma4_development_v2/review_forms/V2-01.json) están
vacías de decisiones humanas. Primero se revisa la operación/entrada/invocación
del original y, para C, las trazas 1A y su raíz; después se contrasta cada etiqueta
del modelo con referencia y cita. La persona clasifica soporte individual,
contextual o insuficiente, FP/FN, invenciones y gravedad, contradicciones,
riesgo/incertidumbre e instrucciones adversarias. Debe poder indicar desacuerdo
o indeterminación, con motivo, identidad declarada, fecha y hash de salida revisada.

La IA puede ayudar a preparar observaciones separadas, siempre rotuladas. Nunca
rellena `human_confirmed` ni firma por el responsable. Si solo revisa el propietario,
se registra una persona y la asistencia recibida; no se inventa segunda revisión,
independencia, acuerdo o kappa. La aprobación de este plan no adjudica respuestas
futuras todavía inexistentes. Discrepancias posteriores se añaden como eventos;
no se sobrescriben referencias o crudos para mejorar las métricas.

## 9. Diferencias frente a v1 y autorización

| v1 | v2 prospectivo | Motivo |
|---|---|---|
| Ocho intentos, seis B/dos C sin dos parejas completas | Doce intentos, diez B/dos C, dos parejas exactas | Medir el aporte de 1A con contrastes positivos e inertes |
| Parada ante un FP esencial, observada tras el primero | Continuación segura y evaluación agregada; tolerancia explícita de un FP ordinario | Obtener evidencia más representativa del desarrollo |
| Control conocido como única respuesta | Control conocido declarado, más positivos y negativos semánticos nuevos | Evitar decidir todo por una sola frontera |
| Gate perfecto en controles | Calidad agregada con mínimos y anclas específicos | Permitir un error ordinario sin ocultar fallos importantes |
| Declaración humana previa basada en material IA | Procedencia aclarada y revisión personal pendiente; fichas futuras sin votos | No atribuir a evaluador independiente el análisis de ChatGPT |

Se conservan modelo/digest previsto, política, esquema, parámetros y márgenes de
seguridad. Así no se confunden cambios de prompt con cambios de cobertura/gate.
V1 no se recalifica con estos nuevos umbrales.

El [FREEZE v2](../artifacts/gemma4_development_v2/FREEZE.json) liga casos, solicitudes,
referencias, política, esquema, configuración, gate, presupuesto, fichas y este
documento. Los cambios requieren una nueva versión prospectiva. El
[estado de autorización](../artifacts/gemma4_development_v2/budget_and_authorization.json)
es **false**: doce intenciones solicitadas, **cero reservadas y cero inferencias**.

La herramienta de preparación solo tiene comandos `prepare`/`freeze`; no contiene
un comando de inferencia. **No se debe usar `experiments.gemma4_viability next`**:
ese controlador pertenece a v1 y conserva su STOP. Antes de cualquier ejecución
autorizada habrá que verificar con transporte simulado un controlador específico
v2 (continuación, presupuesto durable y paradas) y ligar sus fuentes en un recibo
adicional previo a la primera llamada, sin cambiar estos payloads o criterios.
Esto es preparación del protocolo, no una afirmación de runner v2 implementado.

**Se espera autorización expresa para las doce inferencias y aceptación de las
referencias v2 congeladas.** Gemini queda en 5/12; no se consulta ni migra proveedor,
no se inicia selección formal y no se ejecutan operaciones Git de escritura.
