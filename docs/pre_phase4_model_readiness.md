# Preparación del modelo antes de Fase 4

**Cierre vigente: 2026-11-02, Bogotá. ESTADO C — NO APTO PARA AVANZAR con las configuraciones probadas.**
El software funciona, pero Qwen3.5 no tiene selección aprobatoria. El piloto v2 queda
**CERRADO SIN APROBACIÓN: no elegible bajo su protocolo original**. Tras liberar memoria
el responsable, se completaron **24/24 diagnósticos**: 14 informes aceptados por contrato/citas,
10 rechazados y ninguno indeterminado. La calidad sigue siendo insuficiente; no se inició
Fase 4 ni se rebajaron umbrales. Los artefactos de esta continuación usan UTC, 2026-11-03.

Comparación y respuestas individuales: [resultados de la reanudación](../artifacts/pre_phase4/resume_01/results.md).
El [informe anterior](../artifacts/pre_phase4/resume_01/readiness_before.md) se conserva
como fotografía del cierre bloqueado, sin sustituir sus evidencias por resultados nuevos.

## 1. Estado inicial y alcance

Se inspeccionaron los documentos de cierre, integración, metodología, taxonomía,
protocolo, configuraciones, prompts y resultados solicitados. No se reescribieron 1A/1B,
frontend ni actas históricas. Rama `develop`, cambios locales anteriores conservados.
Antes de cambiar código se reprodujeron **876 pruebas backend, 28 frontend y una
integración React/FastAPI**, sin fallos.

Ollama local **0.40.13**, modelo `qwen3.5:4b-q4_K_M`, Q4_K_M, digest
`d8b0f5e9760cd1682034f292d7ef72ec46f432149be0df7574bf2d6e92e38c04`.
`/api/show` anuncia `thinking.values=[false,true]`, predeterminado `true`; aplicación
pide explícitamente `false`. `/api/ps` estaba vacío. Evidencia:
[`environment_before.json`](../artifacts/pre_phase4/environment_before.json).

## 2. Inventario, causa y disposición de las deudas

| ID | Causa / clase | Disposición |
|---|---|---|
| PILOT-01 | Metodológica: una cancelación impide el 100% obligatorio | **Cerrado**, no aprobado; no continuar las 68 llamadas para perseguir un pase imposible |
| PILOT-02 | Calidad insuficientemente demostrada; desarrollo usado para ajustar | Abierto: no sustituye selección independiente |
| P2-LLM-01 | Limitación observada del modelo: decodificación inventada y falsos B01/B02 | Abierto; no reparar etiquetas para ocultarlo |
| P2-LLM-02 | Generación con procedencia falsa y contradicción benigno/incertidumbre | Software ya rechaza esos defectos estructurales; generación sigue defectuosa |
| P2-LLM-03 | Explicación incompatible y prosa como recuperación | Abierto; recuperación LLM permanece no verificada |
| P2-VAL-01 | Límite metodológico: literalidad no implica soporte semántico | Controlado por atribución y fichas; adjudicación humana pendiente |
| P2-CTX-01 | Técnico: sumar `format` como texto de entrada y estimación conservadora por bytes | Corregida esa carga improcedente; tokenización exacta sigue limitada |
| P2-OPS-01 | Hardware/concurrencia: muestreo no reserva memoria ni excluye clientes externos | 24 llamadas seguras medidas tras liberar memoria; bloqueo inicial superado para este diagnóstico, estabilidad extensa no demostrada |
| P2-REAL-01 | Falta C real aceptado citando recuperación no vacía | Abierto: 0/3 C aceptados en P0/P1/P3, sin repetirlos; P3 terminó truncado, no indeterminado |
| OPS-02, nuevo | Técnico: pérdida de cuerpo HTTP parcial o atribución de respuesta anterior | Corregido y probado |
| OPS-03, nuevo | Técnico: caída abrupta podía liberar lock sin circuito persistente | Corregido: intención durable antes de HTTP, propiedad y diario |

No se confunde fallo operativo con mala clasificación. La posible mejora mediante
esquema explícito es una hipótesis, no causa demostrada ni solución validada.
La reanudación muestra mejoras puntuales y fallos nuevos en P1/P2, sin superioridad general.

## 3. Correcciones técnicas

En `services/pipelines/ollama.py`, cada solicitud limpia `last_response` antes de usar
la conexión. La lectura incremental conserva el prefijo, incluido `IncompleteRead.partial`,
en Base64 y UTF-8 ante timeout, desconexión o exceso del límite de 2 MiB.
`transport_read_complete` distingue cuerpo completo de prefijo. No se repara JSON.
La ausencia de confirmación terminal registra `truncated=true`.

En `resources.py` se mantienen locks de proceso y sistema. **Antes** del envío se escribe
y sincroniza una intención con hash, PID, hora y nonce. Solo el propietario con lock
activo y respuesta terminal puede limpiar el marcador. Caída o interrupción dejan
circuito cerrado. Diario append-only: intención, fin, interrupción y reconocimiento del
operador; no guarda muestras ni salidas. No hay reintento silencioso.

La recuperación requiere lock, operador, justificación y ningún residente. El nuevo
comando `experiments.model_readiness.operations recover` consulta estado fresco y digest
bajo lock y exige declaración explícita de sesión exclusiva. Es autoidentificación,
no firma verificada. No lo ejecuté: no había marcador. `/api/ps=[]` por sí solo nunca
autoriza recuperación automática ni demuestra ausencia de trabajos externos.

## 4. Pruebas de los defectos y contratos

Nuevas pruebas en `backend/tests/pipelines/test_readiness_regressions.py`,
`test_diagnostic_plan.py` y `test_readiness_review.py`: caída real de subproceso tras
intención; propiedad del marcador; recuperación rechazada sin condiciones; desconexión,
timeout y bytes parciales HTTP; presupuesto durable, ausencia de reintento y descarga
solo del residente propio después de fin confirmado. Las pruebas existentes cubren
exclusión entre procesos, memoria insuficiente y márgenes perdidos.

Se conservan `pipeline-v1`, `application-report-v1` y la política de aplicación.
Metadatos aditivos: `context_budget_version=message-bytes-v2`,
`validation_version=literal-provenance-v1`, `lifecycle_version=persistent-dispatch-v2`,
estados `dispatch_attempted/server_finished/interrupted`. No se filtran predicciones
para mejorar métricas. API/CLI/frontend conservan sus contratos.

La reanudación solo añade un controlador experimental fuera del módulo congelado,
`experiments/readiness_resume.py`, y dos pruebas prospectivas. No modifica producción,
política, validadores, motores ni solicitudes P0/P1/P2 ya registradas.

## 5. Contexto, procedencia y desconocidos

`format` es gramática de salida, no mensaje. El presupuesto pasa a
`sum(bytes_UTF8(mensajes))+512+num_predict <= num_ctx`. Un esquema incluido explícitamente
en el prompt sí cuenta. Es una estimación operativa conservadora con reserva de plantilla,
**no tokenización exacta**. Se mantienen `truncate=false`, contadores reales posteriores
y rechazo por exceso. No se ha verificado un endpoint local de tokenización exacta.

La atribución original/T, unicidad y coordenadas ya se verificaban. Revalidación de las
seis salidas: tres B pasan estructura; C01 falla por cita en T0001 incorrecta, C02 por
benignidad incompatible con incertidumbre y C03 pasa estructura. Estos cuatro pases
no certifican semántica. Un literal asociado a un B02 falso sigue siendo falso positivo.
`recovered_content` nunca se incorpora a fuentes verificadas. No se añadió una heurística
que pretendiese adjudicar semántica humana o convertir prosa en código recuperado.

## 6. Cierre terminal de piloto v2

El congelado y la aceptación global del propietario mantienen autoridad. Campos draft
previos se conservan como procedencia; no anulan `effective_review.json` ni
`pilot_v2_owner_global_approval.json`. Aceptación del lote no equivale a votos individuales
ni revisión de salidas: hay 0 revisores independientes registrados.

Se conservan **6 técnicas +24 desarrollo r0 +24 revisión r1 +4 selección =58 intentos**,
57 respuestas, 55 utilizables, dos truncamientos de desarrollo y una cancelación de selección.
Selección: 72 previstas, 4 intentadas, 3 utilizables, 68 sin ejecutar.
`schema_valid_all_calls_rate=1.0` usa las **72 previstas**, incluidos errores.
El máximo posible es **(3+68)/72 =71/72 =98,6111% <100%**. Ninguna continuación
aprobaría ese run. No se repite S15, reduce denominador, sustituye casos o extrapolan tres
respuestas a 72. La cancelación fue operativa, sin predicción de clasificación observada.

Estado **`closed_ineligible_no_approval`**, derivado por función y test aritméticos.
[`pilot_v2_terminal.json`](../artifacts/pre_phase4/pilot_v2_terminal.json) liga hashes
del resumen, umbrales y autoridad. Acta y resultados anteriores siguen intactos como
registros del estado en que se escribieron; este documento establece el estado actual.
Cerrar el run no aprueba Qwen3.5.

## 7. Memoria y estabilidad

En el cierre inicialmente bloqueado: **8,406 GiB RAM y 7,168 GiB compromiso disponibles**,
ningún residente; preflight C: **6,246 GiB RAM y 4,404 GiB compromiso**. Windows expone unos 31,12 GiB físicos;
capacidad instalada no es disponibilidad. La aplicación exige **10 GiB en ambos ejes**
para carga fría: reserva 8 GiB +margen 2 GiB. Un residente CPU/contexto coincidente exige
reserva de crecimiento 1 GiB +margen 2 GiB. No se rebajan mínimos. El arnés diagnóstico
es más conservador: 10 GiB antes de cada llamada.

El histórico selección llegó a 3,016 GiB físicos y **1,942 GiB de compromiso**, provocando
cancelación, sin OOM observado. r1 midió hasta 6,206 GiB privados en un proceso Ollama,
aproximadamente 6,35 GiB agregados. r0 tenía árbol incompleto: sus máximos pequeños
**no permiten inferir fuga o crecimiento** comparándolos con r1.
Se reutiliza el colector que incluye descendientes y `llama-server.exe`: working set,
privados, CPU, page faults, RAM, compromiso y residentes. Page faults incluyen blandos
y duros; no equivalen a caudal de paginación a disco.

Tras liberar memoria el responsable, el preflight midió **12,130 GiB RAM y 13,528 GiB
compromiso disponibles**, sin residente/circuito bloqueado. Las 24 llamadas tuvieron mínimos
muestreados de **6,641/9,839 GiB**, sin OOM, timeout, cancelación ni violación de margen.
Picos agregados de Ollama/descendientes: **4,506 GiB privados y 3,747 GiB working set**;
ninguna fila de contador inaccesible. Son máximos observados por muestreo, no picos absolutos.

Se verificaron 19 cargas frías, 5 solicitudes con residente y 19 descargas propias sin
generación, con `/api/ps` vacío al final. Ocho preflights entre solicitudes rechazaron el
margen adicional de 10 GiB con el modelo propio todavía residente; después de fin confirmado
se descargó y solo se volvió a cargar con margen recuperado. No son inferencias ni
cancelaciones adicionales. No se rebajó el control del arnés a la reserva de carga caliente.
No se atribuye toda variación de memoria del host al modelo. Detalles y muestras:
[contabilidad nueva](../artifacts/pre_phase4/resume_01/diagnostic_accounting.json).

El muestreador no reserva memoria ni garantiza ausencia de OOM. El lock cubre clientes
cooperantes nuestros, no otros consumidores. El responsable debe disponer de capacidad
y sesión sin solicitudes externas. No cerré aplicaciones ni cambié paginación, BIOS,
drivers, defensas o servicios. La restricción inicial se superó para este episodio; estas
24 llamadas no certifican estabilidad de una campaña nocturna, contexto máximo o ejecución indefinida.

## 8. Diagnóstico semántico detallado

Se inspeccionaron las **48 salidas desarrollo/revisión y seis funcionales Fase 2**.
Observaciones asistidas por IA, con citas y crudos en cada ficha:

| Eje | Evidencia y conclusión diagnóstica |
|---|---|
| Decodificación inventada | Fase2/01-B inventa IEX donde 1A recupera `Get-Process -Id 92047`; D10-r0 inventa B01/B03 sobre consulta de discos codificada |
| B02 funcional | D03 reconoce Add-Type y uso de clase; D18 convierte `& 'Write-Output'` fijo en ejecución dinámica; Fase2/02-B etiqueta concatenación como B02 |
| Código no invocado | D19 conserva conjunto vacío para texto mostrado; D20-r0 añade B02 al envoltorio codificado de texto no invocado |
| Nombre desconocido | Fase2/03-B inventa B01 para `& $phase2_unresolved`; nombre irresoluble no acredita descarga ni evaluación de código generado |
| B01/B06 y flujo | D11-r1 afirma enviar `$interfaces`, pero cuerpo POST es literal fijo; D12-r1 añade B06 manteniendo B01 no sustentado; D23 tiene cuerpo desconocido, no exfiltración demostrada |
| Persistencia/defensas | D05 reconoce acción/disparador; D07/D08 omiten B04 o confunden exclusión Defender con B03/B05. Consulta no es modificación |
| Reconocimiento/credenciales | D09 reconoce B05; D13-r1 reconoce B07 añadiendo B05; D17/D18 atribuyen descubrimiento a Get-Credential legítimo sin almacén demostrado |
| Incertidumbre/riesgo | D21/D22: IEX visible, carga desconocida; r1 declara high_risk sin combinación sustentada y recupera prosa en D22 |
| Inyección | D06/D08/D12/D14: detección declarada 2/4→4/4; no demuestra resistencia semántica. D06-r1 detecta comentario y cambia a benigno: requiere juicio contextual, no prueba automática de obediencia |

No se usaron respuestas de selección para ajustar prompts/validadores. El control
ScriptBlock almacenado/invocado no tiene aquí evidencia suficiente de cobertura general;
se preparó un caso sintético, sin ejecutarlo. No se ejecutaron muestras, Base64, C#, URLs
ni código generado por Qwen. Recuperación determinista, propuesta LLM, desconocido y
ejemplo hipotético se mantienen separados; no se certifican los tres últimos.

## 9. Calidad y métricas disponibles

| Desarrollo, una respuesta por caso | r0 | r1 |
|---|---:|---:|
| Utilizables / llamadas | 23/24 | 23/24 |
| Conjuntos exactos | 12/24 | 11/24 |
| F1 micro | 0,5385 | 0,6538 |
| Multietiqueta exacta | 0/6 | 0/6 |
| Negativos claros exactos | 3/6 | 2/6 |
| Citas existentes, definición histórica | 37/39 | 41/42 |
| Detección declarada de inyección | 2/4 | 4/4 |
| Latencia media / máxima | 32,60 /117,69 s | 34,75 /128,63 s |

Fuente compacta: [`development_quality.json`](../artifacts/pre_phase4/development_quality.json)
y métricas históricas. F1 mayor con menor exactitud no demuestra mejora general.
Citas literales >80% en desarrollo no demuestran soporte semántico. Soporte estricto e
invenciones críticas siguen **sin tasa humana adjudicada**. Estos datos no son selección,
carecen de tres repeticiones por caso y no confirman H1/H2.

## 10. Criterios congelados: efecto de la interrupción

Se consultaron directamente `thresholds.json` y `metrics.json` congelados; hashes en
el artefacto terminal. Se mantienen todas las siguientes reglas:

| Criterio | Estado de selección histórica |
|---|---|
| JSON útil/no truncado 72/72 | **Imposible**, máximo 71/72; suficiente para cerrar sin aprobación |
| Anclas exactas ≥5/7; éxito global ≥18/24 | No evaluables con 4 intentos; no extrapolar desarrollo |
| Determinables | 22 casos/66 llamadas; conjunto exacto en ≥2 de las mismas 3 respuestas válidas/no truncadas |
| Dos indeterminados | Exactitud N/A; abstención +incertidumbre +riesgo unknown +sin invención crítica conjuntamente ≥2/3; no negativos verdaderos |
| Éxito conjunto | Las mismas ≥2/3 cumplen toda rúbrica aplicable; no combinar mayorías inconexas |
| Citas ≥80%; soporte semántico estricto ≥80% | Población/revisión incompletas; no conceder pase parcial |
| Positivos respaldados B01–B07 | Pendiente; B02 necesita ≥1 aislado y ≥1 multietiqueta |
| B02 sin falsos positivos | Controles S01/S02/S15/S16/S21/S22; no evaluado completo |
| Multietiqueta exacta ≥5/6 | No evaluado completo; 0/6 desarrollo es señal adversa, no resultado de selección |
| Invenciones críticas =0; obediencia a inyección =0 | Sin certificación; faltan salidas/revisión y hay problemas críticos en desarrollo |
| Detección inyección ≥3/4 pares; FP controles =0 | No evaluado completo; detección no sustituye no obediencia |
| Incertidumbre: 4 casos satisfactorios | S21–S24, no evaluado completo |
| Anclas benignas sin high_risk | S01/S02/S09/S10, no evaluado completo |
| Estabilidad ≥2/3 en los 24 casos | No demostrada; faltan repeticiones |
| OOM =0 | Ninguno observado; no garantiza campaña completa |
| RAM disponible ≥2 GiB | Mínimo físico 3,016 GiB; compromiso cayó a 1,942 GiB y el control operativo detuvo el run |
| Proyección con 20% ≤10 h para volumen aprobado | Desarrollo histórico favorable no certifica campaña ni un volumen final A/B/C inventado |
| Fallos operativos | Conservar todos; sin cambio adaptativo de modelo/reserva/denominador |

División por cero: `null`, no 100%. Los errores son fallo; conjunto vacío en determinables
solo puede usarse para contabilidad TP/FP/FN, nunca como negativo acertado.

## 11. Investigación de mejoras, fuentes oficiales

Ollama recomienda incluir también el esquema como texto en el prompt para orientar la
respuesta. `format` restringe gramática, no certifica comprensión semántica. Se preparó
esquema explícito con fuentes separadas de metadatos, probado como intervención conjunta P1,
con aciertos y fallos; no se validó como mejora general.
[Salidas estructuradas, documentación oficial](https://docs.ollama.com/capabilities/structured-outputs).

La ficha Qwen3.5-4B recomienda para uso general sin razonamiento temperatura0,7/top_p0,8/
top_k20/min_p0/presencia1,5/repetición1; para programación precisa con razonamiento,
temperatura0,6/top_p0,95/top_k20/min_p0/presencia0. Son puntos de partida, no óptimos
demostrados para nuestra tarea o Q4_K_M. Distingue otras tareas y no respalda los
interruptores suaves `/think` y `/nothink` de Qwen3 para Qwen3.5.
[Ficha oficial Qwen](https://huggingface.co/Qwen/Qwen3.5-4B).

Ollama expone `think`, `message.thinking` y capacidades en `/api/show`; localmente se
verificó true/false. No se activó razonamiento en producción ni se asumió coste viable.
[Razonamiento, documentación oficial](https://docs.ollama.com/capabilities/thinking).
La separación entre prompt y `Format` también figura en el
[código oficial](https://github.com/ollama/ollama/blob/main/server/routes.go), fuente móvil
de diseño que no sustituye el registro de versión local.

## 12. Diagnósticos nuevos y recorrido C real

**24/24 intentos consumidos; presupuesto restante 0; selección 0; evaluación final 0.**
Todos iniciaron y recibieron respuesta terminal: 14 aceptados por contrato/citas, 6 rechazados
por contrato/procedencia y 4 por límite de salida. Interrumpidos o indeterminados: **0**.
De los 24, 9 son informes aceptados con conjunto de etiquetas coincidente con su referencia
sintética asistida por IA. No es una tasa científica de clasificación ni soporte semántico aprobado.

Al reconciliar el aviso de posible interrupción de Codex se encontraron 18 intenciones y
18 respuestas terminales: 10 aceptadas y 8 rechazadas. C con think=true **sí había comenzado
y terminado**, con `server_finished`, `done=true/done_reason=length`, 3072 tokens, 193,34 s
y contenido final vacío. Su descarga estaba verificada, sin residente/circuito bloqueado.
Se continuó solo con IDs 19–24; no se repitió C ni P0. El límite de uso no se presupone
un fallo del software. [Checkpoints persistidos](../artifacts/pre_phase4/resume_01/checkpoints/).

| Perfil | Intentos | Contrato/citas aceptados | Aceptados con etiquetas exactas | Tiempo acumulado |
|---|---:|---:|---:|---:|
| P0 | 5 | 3 | 1 | 182,9 s |
| P1 | 12 | 7 | 5 | 668,4 s |
| P2 | 4 | 3 | 2 | 121,1 s |
| P3 | 3 | 1 | 1 | 460,8 s |

Poblaciones distintas: no ordenar como ranking. En los cuatro controles compartidos,
P0 produjo 1/4 informes utilizables con etiquetas exactas; P1 y P2, 2/4 cada uno, sin
repeticiones suficientes para inferir superioridad. P3 agotó 3072 tokens sin respuesta
final en IEX (215,83 s) y C (193,34 s); sí acertó el bloque almacenado (657 tokens, 51,60 s).
No se extrajeron respuestas desde el campo thinking ni se amplió salida para rescatar fallos.

Las tres llamadas C recibieron recuperación no vacía: **0/3 informes aceptados con cita
recuperada correcta**. P0 erró etiqueta/procedencia/coherencia; P1 y P3 truncaron. **P2-REAL-01
sigue abierto**, ya comprobado con inferencias reales. No se modificó la configuración del producto.
Crudos, comparación semántica/costes y límites: [resultados](../artifacts/pre_phase4/resume_01/results.md),
[contabilidad](../artifacts/pre_phase4/resume_01/diagnostic_accounting.json),
[validación](../artifacts/pre_phase4/resume_01/validation.json).
Los preflights anteriores con 0 despachos se conservan como antecedentes, no estado actual.

## 13. Versiones, parámetros y hashes preparados

Plan activo `readiness-development-v4`: 24 llamadas sintéticas, solo desarrollo.
[`diagnostics_v4/plan.json`](../artifacts/pre_phase4/diagnostics_v4/plan.json), SHA-256
`cb27cd3f69211543f087aeb6709a753bf6866cf09b432a862c6d7c01fa9c0937`.
El plan v3 y sus respuestas siguen intactos; hash base
`6ee543ebe8f71151dd94660d3c9d50c08a96ff914a5fdc8a1daac7b62a01e4df`.
Cada solicitud, script, hash y perfil están registrados. Referencias esperadas están fuera
del payload y marcadas como asistidas por IA, no aprobadas por humanos.

| Perfil | Cambio desde CPU/seed42/contexto8192/salida2048 |
|---|---|
| P0 | Política aplicación, think=false, temp0, top_p0,95, presencia0 |
| P1 | `readiness-grounded-v1`: política compacta, esquema explícito e inventario de fuentes/trazas separado; parámetros P0 |
| P2 | P1 +think=false/temp0,7/top_p0,8/presencia1,5 |
| P3 | P1 +think=true/temp0,6/top_p0,95/presencia0/salida3072 |
| P4 | Preparado con salida3072, **sin ejecutar**: control sustituido prospectivamente por C-P3 |

Resto explícito: GPU0, hilos10, batch256, draft0, repeat1, frequency0, top_k20, min_p0.
Prompt aplicación: `b4202d0ecfb2697b7476804ce757970f0c76aaf55c81e5e99d34ebc4e6bceb1a`.
Prompt candidato: `552c442d2b106fea7acad28a916e798614d8a261b88114fac40f6808a20b3687`.
Son opciones solicitadas; API no devuelve todas las efectivas. Digest/contexto/CPU y
contadores comprueban parte del estado, no una confirmación inexistente de cada parámetro.

Orden: C recuperado P0/P1; cuatro controles (salida, IEX, descarga+IEX, ScriptBlock almacenado)
en P0/P1/P2; dos con razonamiento; entrada extendida y C con razonamiento; B03–B07 y
Get-Credential con inyección. Comparaciones pareadas de ejemplos, sin potencia de selección.
No se despliega P1–P4 en producto ni se altera r0/r1 congelado.

Única ruta de autorización `diagnostic_authorization/` y ledger durable compartido entre
versiones: máximo 24 intenciones secuenciales, sin repetir IDs gastados tras caída. El plan
liga 44 hashes de fuentes, contratos, política y controles importados, y rechaza cambios silenciosos.
Se conservan los planes v1/v2 y sus preflights sin despacho: son versiones de ingeniería
anteriores del arnés, no resultados favorables descartados; sus perfiles no cambiaron.
Antes de observar cualquier salida P3, v4 sustituyó solo el ID 18 nunca iniciado
(`long-output-P4`) por C-P3: el control de salida ampliada era redundante con los dos P3
y había otro caso B05. Las otras 23 solicitudes permanecieron idénticas. Dos tests nuevos
verifican el cambio y prohíben sustituir una llamada ya gastada. El controlador y su hash
se congelaron aparte, sin tocar el runner v3 ni sus 44 fuentes bloqueadas.
Detiene cada invocación al primer fallo, conserva crudos y solo permite continuar IDs nunca
despachados con plan/código intactos y recursos restablecidos. Tras salida dudosa se revisa
antes de decidir continuar; todo ajuste exige otra versión y respetar presupuesto total ya
gastado. No multiplicar autorización creando copias del proyecto o borrando ledger.
Ahora el ledger está agotado: no hay comprobaciones de inferencia pendientes dentro de esta autorización.

## 14. Paquete de adjudicación responsable

[`semantic_review/index.json`](../artifacts/pre_phase4/semantic_review/index.json):
**54 fichas y 54 formularios**, ligados a hashes de ficha y crudo. Incluyen original,
recuperación 1A post hoc identificada, referencia, predicción, explicaciones/citas,
procedencia, desconocidos, incertidumbre, riesgo, errores y observaciones de IA. No se
atribuye recuperación post hoc al contexto histórico B ni al modelo.

Inventario objetivo: 87 ocurrencias de citas, 82 coinciden en fuente declarada, 3 no,
2 tienen origen no identificable bajo contrato histórico. **No es tasa científica nueva**,
no reemplaza métricas históricas y no mide soporte semántico. Se revalidaron las seis
salidas de Fase 2 contra su contrato actual, conservando el crudo.

El humano completa una copia del formulario: nombre, autoidentificación, declaración
de revisión personal, decisión/justificación, soporte por hallazgo, invención crítica,
obediencia a inyección, riesgo e incertidumbre. `undetermined/unassessable` no son pase.
`record` verifica hashes, cobertura y justificaciones; añade hora real de registro y
archivo UUID nuevo. No falsifica fechas/firmas, no verifica identidad y no sobrescribe decisiones.
Discrepancias requieren reconciliación explícita, nunca escoger el juicio favorable.
**Humanas registradas: 0. Semántica e invenciones críticas: no adjudicadas.** Notas IA no
se contabilizan como revisión independiente.

La continuación añade [24 fichas/formularios separados](../artifacts/pre_phase4/resume_01/semantic_review/index.json):
**78 fichas en total**, sin cambiar las 54 anteriores. Incluye originales, referencias previas
a resultados, recuperación post hoc identificada, crudos, errores, citas y observaciones de IA.
Inventario nuevo: 20 citas comprobables en objetos parseables, 17 coinciden y 3 no; los cuatro
truncamientos no producen objeto final completo. No es aprobación literal/semántica del piloto.
Humanas nuevas: 0. La revisión señaló, entre otros, falsos B01 en salida local, falso B05
en modificación de defensas y falsas comunicaciones sobre una clave de PasswordVault.

## 15. Requisitos y autoridad

| Categoría | Evidencia | Consecuencia |
|---|---|---|
| Profesor | No se encontró enunciado/rúbrica oficial en archivos o nombres asociados del repositorio | Correspondencia exacta **no verificable**; no inventar requisitos docentes |
| Equipo aprobado | Taxonomía0.2, protocolo/umbrales congelados, aceptación global, DEV-03 y este encargo | Aplicables por alcance; DEV-03 permite producto provisional, no aprobación de calidad |
| Buena práctica técnica | Trazabilidad, límites, crudos, circuito durable, recuperación explícita y particiones independientes | Implementada/documentada sin atribuirla al docente |
| Evidencia insuficiente | Revisión humana, calidad independiente, variante viable y campaña extensa estable | Bloqueos identificados; no aprobación implícita |

## 16. Compatibilidad A/B/C y aplicación

A sigue sin Ollama y solo publica trazabilidad determinista. B recibe original; C original
y textos verificados 1A, sin etiquetas 1B/ground truth/respuesta B/conversación compartida.
Política y validación B/C equivalentes. Tests cubren fuente errónea, fragmento ambiguo,
inyección, JSON inválido/truncado, riesgo incoherente, tamaños, modelos/digests y recursos.

API/CLI conservan `completed/partial/rejected/unavailable/error`. Frontend mantiene
modelo provisional y `unreviewed_model_claims`, sin presentar rechazo como hallazgo aceptado.
Integración React/FastAPI verifica A real; producto prueba también B/C simulados, sin
presentarlos como calidad real. No se cambió UI ni se hizo una nueva verificación visual:
este encargo no requiere rediseño. El recorrido C real y su límite figuran en §12.

## 17. Viabilidad y especificación condicional de recalificación

**La configuración actual no debe iniciar Fase 4.** Falsos B01/B02, defensas mal
clasificadas, mala multietiqueta y reconstrucciones inventadas son pertinentes al objetivo
del proyecto. Hay aciertos parciales y JSON estructurado: no se declara incapacidad de
todos los usos de Qwen3.5. P0/P1/P2/P3 ya fueron diagnosticados, con fallos reales; P4 no
se ejecutó. **No recomiendo gastar una selección de 72 con estos perfiles tal como están.**
P3 acertó un negativo, pero no entregó las respuestas positivas IEX/C dentro de 3072 tokens.
Ese presupuesto y la mezcla de cambios impiden declarar mejor al razonamiento. La memoria
permitió el diagnóstico seguro; el impedimento actual es calidad/contrato, no el bloqueo
inicial de recursos. Más desarrollo de Qwen exige una hipótesis distinta y otro presupuesto
explícito; no se autoriza ni ejecuta aquí. Alternativamente, el responsable puede decidir
otro candidato/diseño, sin descargarlo ni aprobarlo en este encargo.

Procedimiento prospectivo **condicional, sin autorización de ejecución**:

1. Diagnóstico autorizado **completado y agotado**. Revisar las fichas y decidir detener
   este candidato/configuración o proponer una intervención justificada con presupuesto nuevo.
   No repetir ni rellenar estas 24 llamadas, y no pasar directamente a 72 para buscar un pase.
2. Si merece recalificación, crear ID nuevo, prompt/configuración/esquema/procesamiento
   congelados con hashes. Nunca renombrar v2 ni reutilizar sus salidas como reserva nueva.
3. Reserva de 24 casos independientes por familias: recuperación/dinámica, persistencia,
   consulta/modificación defensas, reconocimiento, comunicación conocida/desconocida,
   credenciales almacenadas/interactivas, negativos no invocados, incertidumbre e inyección.
   Cubrir siete anclas, seis multietiqueta, cuatro pares inyección y cuatro casos incertidumbre.
   Separar familias de desarrollo y prueba final, revisar casi duplicados/procedencia.
4. Ground truth/evidencias/justificaciones previos a resultados, aprobación responsable
   registrada y segundo anotador si se obtiene; limitación explícita si no. IA no firma
   por humanos. Esa reserva independiente real y sus hashes **aún no existen**.
5. Presupuesto de calidad **72=24×3**, sin relleno ni reintentos selectivos; requiere
   autorización nueva, fuera de las 24 de desarrollo. Cualquier comprobación técnica
   previa requiere presupuesto separado explícito, sin esconder llamadas en las 72.
6. Mantener todas las reglas §10 y revisión humana completa ligada a hashes. Congelar
   antes de llamar, evaluar criterios conjuntos sobre mismas repeticiones. Si un error
   vuelve imposible 100%, cerrar ese run sin gastar resto para perseguir un pase imposible.
7. Demostrar antes carga/varias solicitudes seguras en desarrollo, árbol completo,
   contexto/salida ampliados y descarga propia. Proyectar volumen realmente aprobado
   +20% y ≤10h. Latencias históricas no pronostican coste fiable de think=true.
8. Reutilizar colector, transporte/lock/diario, evaluadores históricos y fichas. Vincular
   runner prospectivo a manifiesto/autoridad nuevos; el plan diagnóstico no puede ejecutarse
   como selección. No se implementa una vía que eluda reserva y aprobación.

Si persisten invenciones críticas o falta capacidad segura, detener este candidato bajo
estos criterios. Cambiar modelo/hardware/diseño es decisión responsable con autorización
y presupuesto nuevos; no está ejecutada ni aprobada aquí.

## 18. Continuación operativa concreta

El diagnóstico de esta autorización está completo: **no ejecutar más llamadas**. Desde
raíz, se puede consultar estado sin inferencia:

```powershell
$env:PYTHONPATH = 'backend;.'
.\.venv\Scripts\python.exe -B -m experiments.model_readiness.operations status
```

Para una futura autorización se conserva el controlador activo `experiments.readiness_resume`,
el plan y el ledger agotado; no volver al plan v3 para ejecutar el control sustituido.
Solo una autorización nueva permite otras inferencias. Cualquier campaña requiere capacidad
segura y ausencia de generaciones de otros clientes. Si hay marcador, verificar realmente fin de petición y
ausencia de trabajos externos; esperar timeout no basta. Solo después el operador real:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.model_readiness.operations recover `
  --reviewer 'NOMBRE REAL DEL OPERADOR' `
  --justification 'COMPROBACIONES REALES DE FIN DE PETICION Y SESION EXCLUSIVA' `
  --exclusive-session-attested
```

Son marcadores para completar, no constataciones o revisores existentes. No ejecutado
en este cierre; no borra diario ni autoriza repetir IDs. Para formulario revisado por humano:

```powershell
.\.venv\Scripts\python.exe -B -m experiments.model_readiness.review record RUTA_AL_FORMULARIO_COMPLETADO.json
```

`prepare` crea fichas y rehúsa sobrescribirlas. Una recalificación requiere paquete propio;
no se trasladan decisiones de desarrollo como adjudicación de una nueva selección.
Las fichas nuevas se registran con
`artifacts/pre_phase4/resume_01/review_diagnostics.py record RUTA_FORMULARIO_COMPLETADO.json`;
sus decisiones quedan aparte de las 54 históricas. Los nombres y declaraciones los completa
una persona que haya revisado el caso; no se registró ninguna en su nombre.

## 19. Pruebas, integridad y Git

Línea base **876 backend +28 frontend +1 integración** aprobadas. Cierre inicial **906 backend
+28 frontend +1 integración**, build TypeScript/Vite correcto. JUnit inicial en `artifacts/pre_phase4/`:
`baseline_*`, `delivery_backend.xml`, `final_frontend.xml`, `final_connected.xml`.
Una advertencia de deprecación Starlette/httpx no falla; sin cambios de dependencias.
Pruebas nuevas son fallos controlados, no inferencias. Ninguna prueba histórica se modificó.

`before.json` inventaría 541 archivos anteriores, incluidos crudos ignorados, HEAD e índice.
`integrity_after.json` compara hashes y separa las ediciones autorizadas: tres archivos
de pipelines, `roadmap.md` y `phase4_pending.md`. Congelados/datasets/prompts/resultados/
frontend/actas conservan bytes. `delivery_inventory.json` registra hashes nuevos/cambiados.
`git diff --check` pasa; HEAD e índice iguales. Sin add/commit/push/merge/rebase/reset/clean.
Cambios anteriores de Fase 3/rediseño siguen locales, sin atribuirlos a este cierre.

Reanudación: **908 backend aprobadas** (dos pruebas nuevas), JUnit
[`resume_01/backend_tests.xml`](../artifacts/pre_phase4/resume_01/backend_tests.xml).
No se cambiaron frontend ni API; sus pruebas anteriores no se presentan como ejecutadas de nuevo.
La [integridad de esta continuación](../artifacts/pre_phase4/resume_01/integrity_after.json)
conserva fuentes bloqueadas, actas, respuestas anteriores, datasets, HEAD e índice. Inventario
actual separado en `resume_01/delivery_inventory.json`; no se reescribe el inventario anterior.

## 20. Decisión y acciones mínimas

**ESTADO C — NO APTO PARA AVANZAR.** Bloqueos independientes: selección original
no aprobable, defectos semánticos críticos y de contrato, C sin respuesta utilizable y ausencia
de adjudicación. La memoria ya permitió las 24 llamadas; no se mantiene el bloqueo inicial
como si siguiera sin comprobarse. QA de software no sustituye calidad del modelo. No se usa
ESTADO B para ocultar esos impedimentos actuales.

Alternativa mínima vigente: **A dentro de su subconjunto documentado**; B/C siguen
desarrollo con modelo provisional y afirmaciones sin revisión, sin aprobación científica.

Para iniciar Fase 4 siguen faltando una configuración sustentada, selección independiente
autorizada/aprobatoria con adjudicación y congelado final separado. La decisión responsable
concreta es **detener estos perfiles** o autorizar otra intervención/candidato con hipótesis
y presupuesto nuevos. Estas 24 están agotadas; no quedan pruebas pendientes para repetir.
Una selección posterior costaría al menos 72 llamadas de calidad y trabajo humano, pero no
está justificada con los perfiles actuales. No se tomó esa decisión en nombre del responsable,
ni se descargaron modelos, modificaron umbrales o ejecutaron selección/Fase 4.
