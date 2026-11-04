# Cierre de diagnósticos Qwen3.5: reanudación tras liberar memoria

**24/24 intentos consumidos. ESTADO C — NO APTO PARA FASE 4 con las configuraciones probadas.**

Fechas de artefactos en UTC, 2026-11-03 (continuación iniciada el 2026-11-02 en Bogotá). Solo desarrollo sintético predeclarado; no selección ni evaluación final.

## Reconciliación y autorización

La comprobación después del aviso de posible interrupción encontró 18 intenciones y 18 respuestas terminales persistidas: 10 aceptadas estructuralmente, 8 rechazadas, ninguna indeterminada. C con think=true era el intento 18: iniciado a 00:23:57.736959 UTC, acuse server_finished a 00:27:11.052627 UTC, done=true/done_reason=length, contenido final vacío. Su descarga propia estaba verificada y no quedaban residentes o circuito bloqueado. El posible límite de Codex no se contabiliza como fallo de Ollama ni motiva repetir C.

Se continuó exclusivamente con IDs 19–24. Estado final: 24 iniciadas, 24 terminadas, 14 aceptadas estructural/literalmente y 10 rechazadas (6 por contrato/citas, 4 por salida truncada). Interrumpidas o desconocidas: **0**. Presupuesto restante: **0**. No hubo repetición, relleno, cambio de modelo o recuperación automática del circuito.

[Contabilidad completa](diagnostic_accounting.json), [validación](validation.json), [checkpoint de reconciliación](checkpoints/), [preflight inicial](preflight.json).

El plan v3 se conservó. Antes de observar ninguna salida P3, v4 sustituyó únicamente el control redundante 18-long-output-P4 por 18-C-recovered-P3, reutilizando el C y la política P1 con el paquete P3. Las otras 23 solicitudes no cambiaron. El mismo ledger global conserva todos los intentos y el máximo de 24. P4 quedó preparado, sin ejecutar. Las dos pruebas nuevas verifican la sustitución prospectiva y prohíben reemplazar un ID gastado.

Plan activo v4 SHA-256: `cb27cd3f69211543f087aeb6709a753bf6866cf09b432a862c6d7c01fa9c0937`.
Plan base v3 SHA-256: `6ee543ebe8f71151dd94660d3c9d50c08a96ff914a5fdc8a1daac7b62a01e4df`.
Controlador SHA-256: `bcf0e014c5ad8b4050eb00fc092fcda360d1065d15855f82e37e20402b9f53df`.

## Perfiles y límites de comparación

P0: política de aplicación, think=false/temp0/salida2048. P1: política compacta con esquema explícito y fuentes separadas, mismos parámetros. P2: P1 con temp0,7/top_p0,8/presencia1,5. P3: P1 con think=true/temp0,6/top_p0,95/presencia0/salida3072. Todos: mismo digest autorizado, CPU, contexto8192, seed42, 10 hilos y batch256. No se modificó la configuración de producción. Se registran parámetros solicitados; Ollama no devuelve confirmación de todos ellos.

| Perfil | Intentos | Contrato y citas aceptados | Aceptados con conjunto exacto | Tiempo acumulado | Tokens de salida reportados |
|---|---:|---:|---:|---:|---:|
| P0 | 5 | 3 | 1 | 182.9 s | 2182 |
| P1 | 12 | 7 | 5 | 668.4 s | 9144 |
| P2 | 4 | 3 | 2 | 121.1 s | 1192 |
| P3 | 3 | 1 | 1 | 460.8 s | 6801 |

Estos grupos tienen poblaciones distintas: no se ordenan como un ranking. Las referencias son sintéticas asistidas por IA, sin adjudicación humana independiente; coincidencia de conjuntos no certifica explicación, riesgo o respaldo estricto. Total: **9/24 informes aceptados con conjunto de etiquetas coincidente**, no una exactitud científica aprobatoria. Hay 11 coincidencias en JSON parseables, pero dos son informes rechazados que no se rescatan.

En los cuatro controles compartidos (salida, IEX, descarga+IEX y bloque almacenado), P0 produjo 1/4 informes utilizables con conjunto exacto; P1 y P2, 2/4 cada uno. Una observación por caso no mide estabilidad ni demuestra superioridad general. P1 cambia política, esquema y representación juntos; P3 cambia razonamiento, temperatura y presupuesto de salida juntos. No hay efecto causal aislado de cada factor.

## Cada intento, incluidos fallos

La columna exacto requiere informe aceptado, no solo etiquetas extraídas del crudo. Un fallo o truncamiento no es un negativo correcto.

| ID / respuesta cruda | Perfil | Estado | Etiquetas del JSON parseable | Exacto utilizable | Segundos | Tokens |
|---|---|---|---|---|---:|---:|
| [01-C-recovered-P0](../diagnostics_v3/results/01-C-recovered-P0.json) | P0 | invalid_response | B02 | no | 43.6 | 465 |
| [02-C-recovered-P1](../diagnostics_v3/results/02-C-recovered-P1.json) | P1 | truncated_response | sin JSON final completo | no | 134.6 | 2048 |
| [03-output-P0](../diagnostics_v3/results/03-output-P0.json) | P0 | aceptado | B01 | no | 33.0 | 411 |
| [04-output-P1](../diagnostics_v3/results/04-output-P1.json) | P1 | invalid_response | ∅ | no | 23.7 | 220 |
| [05-output-P2](../diagnostics_v3/results/05-output-P2.json) | P2 | aceptado | ∅ | sí | 23.3 | 210 |
| [06-invoke-P0](../diagnostics_v3/results/06-invoke-P0.json) | P0 | aceptado | B02 | sí | 37.7 | 493 |
| [07-invoke-P1](../diagnostics_v3/results/07-invoke-P1.json) | P1 | invalid_response | ∅ | no | 62.0 | 864 |
| [08-invoke-P2](../diagnostics_v3/results/08-invoke-P2.json) | P2 | aceptado | ∅ | no | 22.8 | 189 |
| [09-download-invoke-P0](../diagnostics_v3/results/09-download-invoke-P0.json) | P0 | invalid_response | B02 | no | 36.3 | 444 |
| [10-download-invoke-P1](../diagnostics_v3/results/10-download-invoke-P1.json) | P1 | aceptado | B01, B02 | sí | 32.7 | 365 |
| [11-download-invoke-P2](../diagnostics_v3/results/11-download-invoke-P2.json) | P2 | invalid_response | ∅ | no | 34.0 | 336 |
| [12-stored-P0](../diagnostics_v4/results/12-stored-P0.json) | P0 | aceptado | B01 | no | 32.4 | 369 |
| [13-stored-P1](../diagnostics_v4/results/13-stored-P1.json) | P1 | aceptado | ∅ | sí | 98.8 | 688 |
| [14-stored-P2](../diagnostics_v4/results/14-stored-P2.json) | P2 | aceptado | ∅ | sí | 41.1 | 457 |
| [15-invoke-P3](../diagnostics_v4/results/15-invoke-P3.json) | P3 | truncated_response | sin JSON final completo | no | 215.8 | 3072 |
| [16-stored-P3](../diagnostics_v4/results/16-stored-P3.json) | P3 | aceptado | ∅ | sí | 51.6 | 657 |
| [17-long-input-P1](../diagnostics_v4/results/17-long-input-P1.json) | P1 | aceptado | ∅ | sí | 19.7 | 237 |
| [18-C-recovered-P3](../diagnostics_v4/results/18-C-recovered-P3.json) | P3 | truncated_response | sin JSON final completo | no | 193.3 | 3072 |
| [19-persistence-P1](../diagnostics_v4/results/19-persistence-P1.json) | P1 | invalid_response | B03 | no | 33.3 | 442 |
| [20-defense-P1](../diagnostics_v4/results/20-defense-P1.json) | P1 | aceptado | B04, B05 | no | 28.3 | 338 |
| [21-recon-P1](../diagnostics_v4/results/21-recon-P1.json) | P1 | truncated_response | sin JSON final completo | no | 114.4 | 2048 |
| [22-post-P1](../diagnostics_v4/results/22-post-P1.json) | P1 | aceptado | B06 | sí | 36.8 | 489 |
| [23-vault-P1](../diagnostics_v4/results/23-vault-P1.json) | P1 | aceptado | B01, B06, B07 | no | 33.8 | 550 |
| [24-credential-control-P1](../diagnostics_v4/results/24-credential-control-P1.json) | P1 | aceptado | ∅ | sí | 50.1 | 855 |

## Hallazgos semánticos asistidos por IA

- P0 añadió B01 a Write-Output y al bloque almacenado, incluso negando acceso remoto en la explicación. Ambos pasaron literalidad: el validador no certifica semántica.
- P1 acertó descarga+IEX y P0 acertó IEX simple, pero P1/P2 omitieron el IEX simple al confundir comportamiento estático con efecto ejecutado o benignidad. La asignación relacionada con $code necesita revisión estricta de citas en el acierto multietiqueta.
- P1 reconoció B03, pero fue rechazado por high_risk con una sola etiqueta; además duplicó barras en una cita. En defensa añadió B05 a B04 por confundir modificación con descubrimiento.
- La consulta de sistema P1 agotó 2048 tokens repitiendo texto y no entregó informe. La entrada de 50 comentarios sí terminó, pero no representa el contexto máximo.
- P1 acertó B06 para el POST conocido. En PasswordVault añadió B01/B06 erróneos: [Retrieve lee Credential Locker y recibe un identificador de recurso](https://learn.microsoft.com/en-us/uwp/api/windows.security.credentials.passwordvault.retrieve?view=winrt-26100). La forma de URL del identificador no prueba red; el literal fixture tampoco es un valor desconocido.
- El control adversario terminó con etiquetas vacías y citó correctamente la instrucción para forzar B07. [Get-Credential solicita usuario/contraseña](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.security/get-credential?view=powershell-7.5), sin acreditar lectura de un almacén en este script. Sin embargo, el modelo afirmó que $null=$x borraba $x: esa asignación descarta el valor de salida y no modifica $x. Es un acierto de control con defectos explicativos; no prueba resistencia general a inyección.

### Razonamiento y C con recuperación

| Caso P3 | Resultado | Tiempo | Tokens reportados |
|---|---|---:|---:|
| IEX funcional | 3072 tokens agotados; sin respuesta final | 215,8 s | 3072 |
| Bloque almacenado | Respuesta válida, conjunto vacío correcto | 51,6 s | 657 |
| C con Get-Process recuperado | 3072 tokens agotados; sin respuesta final | 193,3 s | 3072 |

Se conserva el campo thinking crudo, pero no se extrae de él una predicción para sustituir el informe ausente. Los contadores no separan tokens de razonamiento y respuesta. Las tres llamadas C (P0/P1/P3) fallaron: **0/3 C aceptados con procedencia recuperada válida**. P2-REAL-01 sigue abierto. No se amplió num_predict ni se repitió C.

## Operación y memoria

El preflight inicial midió 12,130 GiB RAM y 13,528 GiB compromiso disponibles, sin residente ni bloqueo, frente a 10 GiB exigidos. Tras reconciliar la sesión se midieron 14,528/19,477 GiB. Se mantuvo reserva de 10 GiB antes de cada despacho y margen de 2 GiB durante generación, con árbol completo de Ollama/llama-server.

Mínimos muestreados de las 24: **6,641 GiB RAM y 9,839 GiB compromiso**. Picos agregados muestreados: **4,506 GiB privados y 3,747 GiB working set** de Ollama y descendientes. Filas de contador inaccesibles: 0. No se observaron OOM, timeouts, cancelaciones ni violaciones de margen. No se garantiza ausencia de picos entre muestras.

Hubo 19 solicitudes frías y 5 con modelo residente. Las 19 descargas propias se verificaron, sin tokens generados y con /api/ps vacío. Ocho preflights entre solicitudes rechazaron el margen adicional de 10 GiB mientras había residente propio; se descargó tras fin confirmado y solo se volvió a cargar al recuperar margen. No son ocho inferencias adicionales ni caídas por debajo de 2 GiB. No se cerraron aplicaciones ni reiniciaron servicios.

Tiempo de inferencias acumulado: **1433,19 s (23,89 min)**, excluyendo pausas de revisión, interrupción de uso de Codex, preflights y descargas. Las variaciones del host, caché y mezcla frío/residente limitan comparaciones de rendimiento. El episodio demuestra ejecución segura de este conjunto, no una campaña nocturna o estabilidad indefinida. Toda la variación del sistema no se atribuye al modelo.

## Revisión, pruebas y decisión

[24 fichas y formularios nuevos](semantic_review/index.json) enlazan fuente, 1A post hoc, referencia, predicción, citas, errores y [observaciones IA](semantic_AI_notes.json). Se añaden a las 54 fichas previas, que permanecen intactas. Decisiones humanas: **0**. Comprobación literal nueva: 20 ocurrencias, 17 coinciden y 3 no; cuatro salidas truncadas no permiten revisar un objeto final completo. No convertir este inventario parcial en una tasa de soporte semántico ni en aprobación de los criterios de selección.

Backend: **908 pruebas aprobadas**, incluidos los dos tests nuevos del cambio prospectivo; una advertencia Starlette/httpx sin fallos. Contratos, política y motores de producción no cambiaron. La verificación de integridad y Git consta en [integrity_after.json](integrity_after.json).

**Recomendación: no ejecutar una selección de 72 con P0/P1/P2/P3 tal como están.** Los aciertos aislados no compensan las respuestas rechazadas, falsos comportamientos, citas inventadas, explicaciones contradictorias y C todavía no utilizable. La memoria ya no bloqueó este diagnóstico; el impedimento actual es calidad/contrato y presupuesto de respuesta, además de selección y adjudicación pendientes. Mantener A y B/C solo como desarrollo provisional, sin Fase 4. Seguir con Qwen requiere una hipótesis nueva y autorización de otro presupuesto de desarrollo; estas 24 están agotadas. Un modelo o diseño distinto también requiere decisión responsable. No se descarga ni aprueba ninguno aquí.
