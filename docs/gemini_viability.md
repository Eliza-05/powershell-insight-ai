# Viabilidad de Gemini 3.8 Flash ? diagn?stico r2

**Resultado: lote detenido por HTTP 503 en el primer caso; calidad todav?a no evaluada.**
Se envi? una ?nica generaci?n, G03-B, y el endpoint respondi?
`gemini_http_server_error`, HTTP **503**, en **6,501 segundos**. El controlador
se detuvo sin reintentar ni ejecutar los nueve casos siguientes.

**Presupuesto actual: 3/12 reservas usadas: dos metadatos y un intento de generaci?n
fallido. Quedan nueve reservas locales sin utilizar.** No se habilit? facturaci?n,
no se cambi? de modelo, no se migr? el proveedor principal y no se inici? Fase 4.

Este informe reemplaza el estado corriente del informe previo, cuyos bytes se
conservan en [viability_report_before_r2.md](../artifacts/gemini_r2/viability_report_before_r2.md).
Los resultados del primer metadato, segundo metadato, piloto v2 y Qwen permanecen intactos.

## Autorizaci?n, cuota y comprobaciones anteriores al env?o

El propietario autoriz? expresamente diez generaciones del plan r2 y declar? haber
verificado personalmente en AI Studio:

| Dato | Declaraci?n del propietario |
|---|---|
| Proyecto | Default Gemini Project |
| Nivel | Free tier; facturaci?n no activada |
| Modelo | Gemini 3.8 Flash |
| RPM | 5 |
| TPM | 250.000 |
| RPD | 20 |
| Uso mostrado | 0 en el per?odo seleccionado |

La confirmaci?n se registr? a **2026-11-03 02:41:34.146755 UTC**; es el registro de
la declaraci?n recibida, no una lectura independiente del panel. Un per?odo
seleccionado en el panel no garantiza saldo instant?neo ni ausencia de otros clientes.
No se realiz? otra consulta de cuota, modelos, tokens o facturaci?n. El listado
anterior ya hab?a confirmado el acceso autenticado a metadatos y la presencia de
`models/gemini-3.8-flash` con `generateContent`.

Antes de enviar se comprobaron el ledger de dos entradas, su hash y los artefactos
ligados al segundo listado; tambi?n los hashes del c?digo de transporte, las versiones
instaladas, la disponibilidad de la clave desde `.env`, el plan r2, los hashes de
pol?tica/esquema y las dos recuperaciones C no vac?as. La lista r2 coincide exactamente
con la funci?n prospectiva registrada. No se modificaron muestras, etiquetas esperadas,
pol?tica o par?metros. El archivo r2 original conserva su flag prospectivo; la nueva
[autorizaci?n de generaci?n](../artifacts/gemini_r2/generation_authorization.json)
la habilita por separado, ligada a un binding inmutable.

Evidencias: [confirmaci?n de cuota](../artifacts/gemini_r2/quota_confirmation.json),
[declaraci?n de origen](../artifacts/gemini_r2/owner_quota_report.json),
[binding anterior a las respuestas](../artifacts/gemini_r2/binding.json).

## Ejecuci?n y respuesta observada

- Reserva global: **3**, `generateContent`.
- Inicio de reserva: **2026-11-03 02:41:44.028978 UTC** (2 de noviembre, 21:41:44, Bogot?).
- Modelo solicitado: **`gemini-3.8-flash`**, sin alternativa autom?tica.
- Caso: **G03-B**, Base64 decodificado y mostrado sin invocaci?n din?mica.
- Latencia del adaptador: **6,5014295 s**; recorrido completo: **6,514808 s**.
- Estado: **HTTP 503**, categor?a segura `gemini_http_server_error`.
- Run ID: `b2c21445-3baf-4852-a6e5-5186089a5fdd`.
- Respuesta utilizable del modelo: **ninguna**.
- Versi?n efectiva de generaci?n, response ID del proveedor, finish reason y tokens:
  **no informados**, no sustituidos por valores supuestos.

El estado HTTP identifica un fallo de disponibilidad del endpoint de generaci?n.
No se conserv? informaci?n que permita atribuirlo espec?ficamente a saturaci?n,
mantenimiento u otra causa interna. No fue un fallo sem?ntico observado ni una
respuesta del clasificador con etiquetas incorrectas. Tampoco demuestra cuota agotada
ni ?xito de generaci?n; la autenticaci?n del listado y la confirmaci?n del propietario
son evidencias distintas.

Se guardaron la petici?n sint?tica exacta, configuraci?n, hashes, tiempos, intento,
estado HTTP y motivo del rechazo en [G03_B.json](../artifacts/gemini_r2/G03_B.json).
**No hay respuesta cruda del modelo que conservar.** El transporte preexistente
contin?a descartando cuerpos de errores HTTP potencialmente sensibles; por ello el
cuerpo HTTP 503 no est? disponible. Esta es una limitaci?n de trazabilidad de este
intento, declarada expresamente. No se inventa su contenido ni se intenta recuperarlo
con una nueva solicitud. Las salidas de modelo HTTP 200, incluidas las rechazadas
por contrato o truncamiento, s? se capturan completas antes de validarlas; ese camino
solo se verific? con respuestas simuladas en esta ejecuci?n de software.

## Informe por caso, en el orden r2

| Orden | Caso | Etiquetas esperadas, fijadas antes de enviar | Resultado real |
|---|---|---|---|
| 1 | G03-B | Ninguna; decodificar y mostrar texto no es B02 | Intentado; HTTP 503; sin salida del modelo |
| 2 | G03-C | Ninguna; misma muestra con recuperaci?n verificada | No ejecutado tras la parada |
| 3 | G06-B | B05 + B06; no B02 autom?tico por EncodedCommand | No ejecutado |
| 4 | G06-C | B05 + B06, con recuperaci?n verificada | No ejecutado |
| 5 | G01-B | B05 por consulta; sin B04/B07 por consulta/autenticaci?n leg?tima | No ejecutado |
| 6 | G09-B | B02 externo, incertidumbre e inyecci?n detectada | No ejecutado |
| 7 | G04-B | Ninguna; bloque no invocado | No ejecutado |
| 8 | G07-B | B04 por debilitamiento de defensas | No ejecutado |
| 9 | G08-B | B07 por recuperaci?n de credenciales almacenadas | No ejecutado |
| 10 | G05-B | B01 por descarga remota | No ejecutado |

No se salt? al segundo caso para eludir el error ni se sustituy? G03-B por otro ejemplo.
G02-B sigue diferido conforme al plan r2; no se reincorpor? para aprovechar reservas.

**Etiquetas B01?B07, falsos positivos/negativos, multietiqueta, literalidad, procedencia,
soporte sem?ntico, alucinaciones, incertidumbre e inyecci?n: no evaluables en este lote.**
No hubo predicciones observadas. No se presenta exactitud 0/10 ni tasas artificiales
asignando errores de clasificaci?n a los casos no ejecutados. Los flags `valid_json=false`
y `exact_labels=false` del evaluador gen?rico de G03-B indican ausencia de salida
aceptada, no un JSON de modelo observado y mal clasificado.

Las dos C tienen evidencia determinista no vac?a preparada y congelada, pero **ninguna
se envi? a Gemini**. No se ha demostrado un recorrido C aceptado con citas correctas.
Que los tests simulados pasen o que existan textos recuperados no demuestra soporte
sem?ntico del modelo. B03 no tiene un positivo aislado en este peque?o plan, otra
limitaci?n de cobertura para una selecci?n futura.

V?anse [resumen operativo](../artifacts/gemini_r2/summary.json) y
[revisi?n de calidad y ausencia de datos](../artifacts/gemini_r2/quality_review.json).

## Cuota realmente contabilizada

| Concepto | Evidencia |
|---|---|
| Consultas de metadatos hist?ricas | 2; no se repitieron |
| Generaciones intentadas en r2 | 1, fallida con HTTP 503 |
| Respuestas utilizables del modelo | 0 |
| Ledger global | 3 de 12 reservas |
| Reservas locales sin utilizar | 9 |
| Tokens de entrada, salida y pensamiento consumidos por el proveedor | Desconocidos: no se recibieron contadores |
| Saldo real RPD/TPM/RPM posterior | No consultado; no se deduce del ledger |

El intento fallido conserva su reserva, aunque no haya salida de modelo. No se sabe
si Google contabiliza este HTTP 503 de igual modo en su panel. No se afirma saldo RPD
19, consumo de tokens cero ni costo medido cero. La confirmaci?n de Free tier procede
del propietario; el agente no habilit? facturaci?n ni utiliz? herramientas de pago.

El controlador fija al menos **21 segundos** entre inicios, secuencial y sin reintentos,
con una ventana conservadora de 61 s para solicitudes y reserva de tokens. El mayor
presupuesto por solicitud preparado es 11.141 tokens estimados, incluida reserva de
salida, por debajo de 250.000 TPM. Es una cota de bytes y reserva, no tokenizaci?n exacta.
Solo se envi? la primera solicitud; no hubo una segunda generaci?n sobre la que medir
intervalos reales de este lote.

## Equivalencia metodol?gica, privacidad y contratos

Se reutiliza `AnalysisService`, sin tocar los pipelines, el contrato `ModelReport` ni
los validadores. A sigue determinista local; B recibe exclusivamente el original y C
recibir?a el mismo original m?s recuperaci?n de 1A. No se env?an resultados de 1B,
referencias esperadas, criterios del revisor o salidas anteriores del modelo.

Par?metros congelados: temperatura **1**, seed **42**, top_p **0,95**, un candidato,
**4096** tokens m?ximos de salida incluidos pensamientos, thinking **low**, timeout
**60 s**, JSON Schema de aplicaci?n. La pol?tica sigue pidiendo una respuesta final
de hasta 2048 tokens. Son par?metros solicitados; no hay salida que permita verificar
versi?n o uso efectivos. Las configuraciones B/C se prueban id?nticas salvo contexto
adicional de C; no se afirma comparaci?n emp?rica de un par completo en este lote.

Se us? exclusivamente la muestra acad?mica G03-B predefinida. No se ejecut? PowerShell,
no se siguieron URLs de muestras ni se habilitaron herramientas del modelo. La clave
permanece solo en el backend; no se cambi? `.env` ni se expuso al frontend. El cliente
oficial mantiene un intento SDK, transporte sin reintentos, sin redirecciones y URL
HTTPS fija. Los estados de error conservan categor?as y c?digos seguros.

El binding incluye hashes del c?digo, pol?tica, esquema y todos los contextos antes
de la primera llamada. Se verifican antes de cada caso. No se edit? ese runtime despu?s
de observar el HTTP 503. Un intent persistente impide reiniciar silenciosamente el
lote, y el ledger cuenta cada intento antes de la red. Los errores de operaci?n o
seguridad detienen el plan; los rechazos exclusivamente estructurales habr?an sido
conservados y seguidos por el caso siguiente sin repetirlos. Esa pol?tica fue fijada
antes de cualquier respuesta y probada con mocks, sin ajustar criterios a resultados.

## Errores resueltos, persistentes y recomendaci?n

**Resuelto localmente:** la doble descompresi?n gzip que pod?a ocultarse bajo
`gemini_transport_error`, adem?s de su clasificaci?n diagn?stica insuficiente. DNS,
TCP y TLS se verificaron anteriormente y el segundo listado autenticado funcion?.
El HTTP 503 actual se identific? correctamente como respuesta HTTP del servicio;
no se ocult? como un fallo gen?rico de transporte.

**Pendiente observado:** disponibilidad del endpoint de generaci?n para este intento.
**Pendiente sin datos:** calidad B01?B07, respuestas estructuradas reales, citas,
resistencia a inyecci?n, incertidumbre y recorrido C. No hay defectos sem?nticos nuevos
que adjudicar y tampoco evidencia que permita declarar resueltos los problemas de
calidad vistos anteriormente con otros modelos.

**Recomendaci?n: conservar el adaptador, pero no seleccionar formalmente ni migrar
Gemini con esta evidencia.** Un HTTP 503 no permite valorar su capacidad de an?lisis.
El lote autorizado qued? detenido; las nueve reservas no utilizadas no se ejecutar?n
sin una nueva decisi?n expresa sobre c?mo proceder. No se cambi? a otro modelo ni
se repiti? una muestra para mejorar resultados.

Qwen3.5 conserva sus resultados y limitaciones hist?ricas. No hay una poblaci?n,
protocolo completado ni salidas de Gemini que permitan comparaciones estad?sticas,
de exactitud o de velocidad entre ambos. La latencia del error no es latencia de
an?lisis satisfactorio. Este diagn?stico sigue siendo exploratorio, no selecci?n
aprobada ni prueba de superioridad.

Una selecci?n independiente posterior requiere disponibilidad operativa, confirmaci?n
vigente de cuota/privacidad, una autorizaci?n y protocolo separados con trazabilidad
del intento fallido, muestra de desarrollo/selecci?n/evaluaci?n separada, cobertura
suficiente de la taxonom?a, umbrales y denominadores fijados antes de resultados,
modelo/prompt/par?metros congelados y adjudicaci?n sem?ntica humana independiente.
No se inici? el lote completo de 72 llamadas ni la Fase 4.

## Regresiones, archivos e integridad

**965 pruebas backend aprobadas, 28 frontend aprobadas y build TypeScript/Vite correcto.**
`pip check` pas?. Se mantiene una advertencia conocida de deprecaci?n Starlette/httpx.
Las siete pruebas nuevas del controlador verifican orden completo, equivalencia B/C,
no filtraci?n de referencias, ausencia de reejecuci?n, parada por 429/403/transporte/
seguridad, retenci?n de salida rechazada y l?mites de espera, usando exclusivamente
SDK y respuestas simuladas. Ning?n test usa la API real ni prueba calidad cient?fica.

Nuevos fuentes: `experiments/gemini_r2.py` y
`backend/tests/pipelines/test_gemini_r2.py`. Artefactos: `artifacts/gemini_r2/` con
confirmaci?n/autorizaci?n, binding, snapshots previos, resultado, evaluaci?n, resumen,
revisi?n de calidad, JUnit y auditor?as. Documentos actualizados: este informe y la
referencia de continuidad en `gemini_transport_diagnostic.md`. No se cambi? el adaptador,
la pol?tica, esquemas, muestras, etiquetas o par?metros de generaci?n.

[Validaci?n](../artifacts/gemini_r2/validation.json),
[integridad](../artifacts/gemini_r2/integrity_after.json),
[auditor?a de secretos](../artifacts/gemini_r2/security_audit.json).
Los dos primeros registros del ledger y todos los resultados hist?ricos permanecen
id?nticos; solo se a?adi? la tercera reserva autorizada. Trabajo local en `develop`,
sin staging ni operaciones Git de escritura. Ollama y el proveedor predeterminado
permanecen conservados. No se habilit? facturaci?n ni se inici? Fase 4.
