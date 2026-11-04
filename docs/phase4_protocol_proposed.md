# Fase 4 — protocolo prospectivo propuesto

**Estado: preparación autorizada; referencias, congelación aprobada y ejecución pendientes.** No se ha realizado ninguna inferencia nueva. Esta propuesta no aprueba al modelo: el rendimiento bajo, un efecto nulo o un efecto negativo son resultados legítimos. La búsqueda de modelos permanece cerrada.

## Hipótesis originales, sin reformulación

Fuente primaria del proyecto: [methodology.md, sección 1](methodology.md), conservada sin cambios. Sus formulaciones exactas están también registradas con hash en [original_hypotheses.json](../artifacts/phase4_preparation/original_hypotheses.json):

- **H1:** la desofuscación estática previa mejora el F1 en la identificación de comportamientos frente al análisis directo del LLM (C > B).
- **H2:** la desofuscación estática previa reduce las afirmaciones no respaldadas por evidencia (C < B).

No se sustituyen por “el modelo produce JSON”, “C tiene más citas” o “el modelo supera un umbral de aprobación”. La política estricta de evidencias sigue siendo principal y la permisiva, secundaria, conforme a DEC-01. No se declaran H1/H2 satisfechas durante esta preparación.

## Unidades, referencias e independencia

Se proponen **16 scripts sintéticos nuevos**, en archivos UTF-8 `.ps1.txt`, y una comparación pareada A/B/C por texto. Ocho tienen recuperación 1A textual verificada no vacía; ocho carecen de recuperación relevante. Se incluyen B01–B07, positivos B03/B04, descargas y cargas funcionales, credenciales interactivas/almacenadas, construcción almacenada/invocada, controles benignos, comentario adversario y dos conjuntos indeterminados.

La [tabla y las 16 fichas](phase4_references_proposed.md) contienen originales exactos, hashes, etiquetas propuestas, inclusiones/exclusiones, evidencia localizada, recuperación y límites. Las propuestas fueron redactadas antes de consultar 1A; no se usaron etiquetas de 1B ni predicciones B/C para construirlas. El motor 1A verifica texto recuperado, no establece por sí solo la referencia de comportamiento.

La independencia se revisa respecto de datasets, diagnósticos y literales de pruebas anteriores mediante hash, normalización de identificadores/literales, vistas recuperadas, coincidencias estructurales y revisión semántica. El [informe de independencia](phase4_independence_review.md) expone coincidencias y diferencias, no una certificación automática. No se reutilizan los seis textos Qwen14, ni se cuentan simples renombrados como unidades nuevas.

Se agrupan conservadoramente F4-04 y F4-10 en `audit-control`: **16 textos, 15 bloques**, y **14 textos determinables en 13 bloques** para clasificación. Son mecanismos de logging relacionados, aunque uno elimina historial y otro deshabilita registro futuro. Si la revisión personal identifica otras dependencias, debe modificarse esta agrupación y versionarse la propuesta **antes** de congelar. B y C no son muestras independientes entre sí.

La selección es deliberada y de tamaño pequeño, con autoría común e historia de desarrollo conocida por el asistente. Es independiente de las respuestas del LLM a estas entradas dentro del repositorio, pendiente de revisar su novedad lógica; no se demuestra ausencia en el entrenamiento del modelo ni representatividad de PowerShell real.

## Seguridad y alcance de las referencias

El responsable aceptó expresamente archivos de texto, objetivos de laboratorio inexistentes y análisis estático únicamente. No hay ruta de ejecución de PowerShell en el controlador. No se ejecutan archivos, texto decodificado, IL, código compilado o sugerencias del modelo. No se consultan dominios de muestras, bóvedas ni almacenes de credenciales. Las rutas de laboratorio no se crean.

Los positivos B03/B04 describen operaciones solicitadas estáticamente sobre hosts/canales ficticios; **no afirman cambios efectivos**. Los dominios `.invalid`, los canales nunca creados y las credenciales literales de laboratorio no son datos reales. La taxonomía caracteriza operaciones y relaciones visibles, no éxito de efectos o intención maliciosa. Las menciones en comentarios, strings documentales y bloques no invocados no reciben etiquetas por sí solas. Las referencias siguen pendientes de revisión personal, incluida esa interpretación.

F4-15 tiene origen/método/cuerpo de una petición no resueltos; no se fuerza B01 o B06. F4-16 tiene B05 conocida como mínimo y un callback desconocido; no se fuerza B02 ni un conjunto total. Sus conjuntos de referencia son `null`, nunca `[]`. Se evalúa por separado la conservación del comportamiento conocido y la expresión de incertidumbre.

## Tratamientos y configuración

- **A:** `AnalysisService`, desofuscación 1A y reglas 1B deterministas, sin LLM.
- **B:** Qwen14 y el original exacto, sin 1A/1B ni respuestas anteriores.
- **C:** el mismo Qwen14 y original, más las trazas 1A verificadas por el pipeline. Sin etiquetas de 1B ni respuestas de B.

Modelo único `qwen2.5-coder:14b`, Q4_K_M, digest `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`. Se reutilizan política `application-analysis-v1`, taxonomía B01–B07 y contrato JSON `application-report-v1`, sin adaptaciones para aprobar el modelo.

CPU, contexto 8192, máximo 2048 tokens, temperatura 0, seed 42, diez hilos, batch 256, repeat_penalty 1, presence/frequency_penalty 0, top_k 20, top_p 0,95, min_p 0; `keep_alive=5m`, plazo absoluto 300 s, sin streaming, truncamiento de entrada, herramientas, parámetro `think` ni generación especulativa. La [configuración exacta](../artifacts/phase4_preparation/proposal/configuration.json) y las [32 solicitudes exactas](../artifacts/phase4_preparation/proposal/requests/) son parte de la propuesta candidata.

La única diferencia de entrada metodológica es la información 1A de C. Si no hay recuperación textual verificada, se mantiene `verified_texts=[]` y se conservan desconocidos/límites/advertencias reales: no se inventa éxito. Estos ocho controles tienen metadatos y sobrecarga de C, por lo que no se espera identidad obligatoria de respuestas B/C. Se informan por estrato; el contraste principal conserva todos los determinables y los estratos son análisis secundarios prespecificados.

## Orden y presupuesto

**16 análisis A + 16 B + 16 C = 48 resultados previstos y 32 intenciones LLM como máximo.** Una intención cuenta antes de enviar bytes a `/api/chat`, incluso si falla, queda incompleta o se pierde el proceso. Las consultas de metadatos y A no son inferencias. No hay carga/generación de prueba adicional, repetición para mejorar salidas ni ampliación implícita del presupuesto diagnóstico anterior.

El [orden exacto](../artifacts/phase4_preparation/proposal/order.json) usa permutación fija de unidades (semilla 40716); ocho unidades tienen B antes de C y ocho C antes de B (semilla 61407). A precede ambos en cada unidad. Las solicitudes LLM son independientes y sin conversación previa; el resultado de A/1B nunca se transmite. Se verifica en cada pareja el mismo modelo, esquema, política y opciones. No hay repeticiones: no se estimará estabilidad entre ejecuciones.

La fecha, estado frío/caliente y tiempos efectivos se registran. El contrabalanceo mitiga efectos de orden/caché; no elimina contención del portátil ni garantiza causalidad. El límite de generación implica hasta 9.600 segundos de plazos de inferencia (160 minutos), más preflights/A/almacenamiento; no es una predicción de duración ni garantía de completar la campaña.

## Preflight y paradas

Antes del futuro primer despacho y de cada llamada posterior se miden nuevamente RAM disponible, compromiso disponible/límite, memoria física, procesos Ollama, residentes, digest/cuantización, capacidades/contexto, versión y espacio del almacenamiento de modelos. No se reutilizan mediciones de desarrollo como garantía actual.

Umbral frío Qwen14: **15.005.580.032 bytes = 13,9750 GiB** de RAM y compromiso disponibles; incluye 9.100.000.000 bytes de cota de pesos, 1,5 GiB KV f16, 2 GiB de buffers/runtime y 2 GiB de margen. Con el mismo modelo/contexto residente en CPU: 3 GiB disponibles. Piso durante inferencia: 2 GiB de RAM y compromiso, monitor nativo continuo; disco libre mínimo: 2 GiB. Se usan los bloqueos de campaña y aplicación. El primer despacho requiere Ollama sin residentes y constatación de sesión exclusiva; no se descargan ni descargan de RAM modelos automáticamente.

La atestación y los bloqueos no pueden impedir que clientes externos arbitrarios ignoren la exclusión. Si no puede comprobarse estado, recursos, integridad o propiedad del despacho, se detiene sin forzar carga. No se cierra software del usuario ni se modifica paginación, suspensión o configuración permanente de Windows.

Paran la campaña: recursos insuficientes, monitor fallido, pérdida del margen, modelo/digest/capacidad incorrectos, herramienta no autorizada, respuesta no terminal/timeout, alteración de hashes/autorización, almacenamiento fallido o pérdida de contabilidad. Un STOP crítico no se limpia ni se reanuda automáticamente.

Continúan, conservándose intactos: FP/FN, citas rechazadas, JSON terminal inválido y respuesta terminal limitada por salida. Una reconstrucción o atribución errónea se registra como defecto semántico, sin promoverla a fuente. Si se descubre corrupción de fuentes o ejecución no autorizada, es una parada de integridad, no un error ordinario de clasificación. No se solicita una respuesta corregida al modelo.

## Métricas y denominadores

Clasificación principal: los **14 IDs determinables fijados antes de salidas**. TP/FP/FN por B01–B07, precisión/recall/F1 micro, macro sobre clases con soporte positivo de referencia, y conjuntos exactos. Una clase positiva no predicha recibe 0 en el promedio macro de soporte, sin eliminarla por precisión indefinida; el valor por clase queda `null` cuando su denominador no existe. Las clases sin soporte se muestran separadas.

Un informe no utilizable conserva predicción `null`, no un `[]` exitoso: no gana exactitud de conjunto y sus positivos de referencia cuentan como FN de cobertura del sistema. Se informa además usabilidad y métricas secundarias solo de parejas utilizables, sin sustituir el principal. No se presentan etiquetas crudas rechazadas como predicciones publicadas.

A conserva cobertura completa/parcial y límites. Se distinguen coincidencia matemática de conjuntos y exactitud con cobertura calificada (A completo); un parcial vacío no certifica benignidad. Los dos indeterminados no reciben TN o exactitud favorable: se reportan etiquetas conocidas mínimas, abstención de categorías desconocidas, incertidumbre alta y fragmentos desconocidos. Un conjunto vacío no basta para pasar ese control.

Citas: denominador de todas las citas de respuestas crudas parseables, también rechazadas; literalidad única y fuente correcta automáticas; original/recuperada y raíces; soporte individual/contextual estricto, insuficiente o contradictorio por revisión personal. Se registran reconstrucciones inventadas/alteradas y riesgo/incertidumbre como ejes distintos. No se confunde literalidad con apoyo semántico.

Si faltan pasos, los resultados descriptivos identifican ejecutados/no ejecutados y sus denominadores; no se realiza contraste H1/H2 como si la campaña estuviera completa. Se conservan los resultados parciales, sin reintentos oportunistas.

## Contraste prospectivo de H1/H2

**H1:** estadístico principal `F1_micro(C) − F1_micro(B)` sobre los mismos 14 determinables, incluido el impacto de rechazos en el sistema. Diferencias por caso, clase, conjuntos exactos y estratos se describen junto con usabilidad. Es un efecto del pipeline con su validador, no precisión intrínseca del LLM aislado.

Como sensibilidad condicional se intercambian B/C dentro de cada bloque conservando el emparejamiento y se recalcula F1 global para cada asignación (13 bloques determinables: 8.192 asignaciones). La alternativa direccional es C>B. Se prepara también bootstrap pareado por bloques, 2.000 remuestreos con semilla 40716, intervalo percentil de 95 % descriptivo. Las observaciones no se remuestrean separando B y C. La convención para denominador F1 nulo es cero, registrada de antemano.

**H2:** cada salida cruda, incluso rechazada por contrato/procedencia, requiere inventario personal completo de afirmaciones factuales atómicas y deduplicadas dentro de esa respuesta. Se cuenta como no respaldada una afirmación insuficiente o contradicha bajo política estricta. Estadístico principal: diferencia C−B del número de afirmaciones no respaldadas por unidad, agregada por bloque; alternativa C<B. La fracción de afirmaciones sin respaldo y el apoyo permisivo son secundarios, para mostrar dependencia con verbosidad y contexto no citado.

Se prepara intercambio/signo por bloque para H2 (15 bloques, 32.768 asignaciones). Sin revisión personal completa y vinculada a hash no se calcula un resultado semántico favorable. Una salida vacía, ilegible o sin afirmaciones evaluables se marca no evaluable, no como cero errores; H2 puede quedar inconclusa aunque se haya completado el presupuesto. Esa limitación es un resultado admisible, no motivo para buscar otro modelo o repetir la campaña.

Los dos valores p condicionales se presentarán crudos y ajustados por Holm para las dos hipótesis principales, junto con los efectos y límites. No se programó una aceptación automática de H1/H2 ni un “APTO”. La dirección esperada no convierte una diferencia observada en confirmación. La interpretación de significación es condicional a independencia entre bloques e intercambiabilidad bajo nula; con selección deliberada, autor común, 16 textos y baja potencia no se afirma significación poblacional ni causalidad general.

El diseño de permutación pareada se documenta en [SciPy, permutation_test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html); el remuestreo pareado, en [SciPy, bootstrap](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html). La implementación local usa la biblioteca estándar y no necesita instalar SciPy. Esas técnicas no corrigen falta de representatividad, referencias débiles o dependencia no detectada.

## Congelación, autorización y conservación

El `CANDIDATE_MANIFEST.json` es una **fotografía propuesta no aprobada**. Sus revisiones previas se conservan. Incluye dataset, referencias, solicitudes, orden, configuración, política, código y evaluador. Si cambia algo antes de aprobar, se genera otra candidata y la revisión anterior deja de corresponder a ese hash.

Para sellar un `FREEZE.json` futuro se exige revisión personal nominativa de las 16 referencias, seguridad e independencia, fecha posterior a la candidata y hashes de cada caso. `seal` no autoriza generación. Luego hace falta **otra autorización expresa**, ligada al FREEZE y a la revisión, con máximo exacto de 32 intenciones, fecha, declaración del responsable y sesión exclusiva. Las plantillas entregadas tienen todas las aprobaciones en `false`. La instrucción actual de preparación no satisface ese permiso futuro.

Cada resultado conserva original/hash, configuración solicitada, perfil/digest, tiempos/tokens, muestras de recursos, envoltura y bytes crudos, validaciones y errores. Se escribe con creación exclusiva, seguido de checkpoint por hash. El ledger se sincroniza antes de despachar. No hay duplicaciones, sobrescrituras o reanudación silenciosa. Una intención huérfana queda gastada y nunca se repite. Una reanudación posterior solo puede continuar pasos no intentados si no existe STOP crítico, los checkpoints son contiguos y existe autorización específica vinculada al hash del ledger; no borra circuitos de la aplicación.

La evaluación operativa está completa con 16 A y 32 respuestas terminales intentadas/registradas, checkpoints íntegros y sin STOP crítico, aunque la calidad sea baja. La revisión científica se cierra con referencias aprobadas y adjudicaciones completas, indicando cualquier hipótesis no evaluable/inconclusa. No se convierte ausencia de anotaciones en aprobación. Las ocho adjudicaciones históricas Qwen14 siguen separadas y pendientes; tampoco se modifica Gemma, Qwen3.5 o Gemini.

No se realizan solicitudes Gemini (ledger 5/12), descargas, borrados de modelos, cambios de frontend o Git de escritura. La Fase 5 queda pendiente del cierre honesto de esta evaluación y su documentación; no se inicia su rediseño en esta preparación.
