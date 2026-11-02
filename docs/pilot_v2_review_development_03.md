> **Estado vigente del lote:** aprobado globalmente por el responsable mediante la [instruccion de cierre](../experiments/reviews/pilot_v2_owner_global_approval.json). Esta ficha/formulario conserva el contenido de preparacion anterior a la congelacion. Sus casillas y estados pendientes son registros individuales historicos, no una nueva exigencia de 48 votos: no hubo revision humana individual independiente. El estado efectivo aprobado se registra por lote; ello no aprueba las salidas del modelo.

# Revision humana — development 3/3

**V2-D17 a V2-D24; ocho fichas, cuatro familias; todas pendientes.**

[Indice de 48 fichas](pilot_v2_cases.md) · [Checklist](pilot_v2_review_checklist.md) · [Metricas y dictamen](pilot_v2_final_review.md)

Las fuentes son texto academico inerte por almacenamiento/procedimiento; no ejecutarlas. Las etiquetas son preliminares del autor asistido por IA.

## V2-D17

**ID:** V2-D17. **Particion:** development. **Familia:** V2-DEV-F09 — Credential object acquisition only.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D17.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D17.ps1.txt). SHA-256: `5a054ad27282a632b8b190dd3662a054a4ce2670f78a4a641521fecb3c796f30`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$login = Get-Credential -Message 'Academic sign-in object; no storage or transmission'
$null = $login
```

**Que hace / justificacion tecnica:** Solicitud legitima de objeto de autenticacion; no se guarda, extrae ni transmite material.

**Lectura de evidencia y condiciones:** Solicitud legitima de objeto de autenticacion; no se guarda, extrae ni transmite material.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Get-Credential por si solo no basta. & invoca Write-Output fijo. No operacion remota.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D17-E01` — `datasets/safe_samples/pilot_v2/development/V2-D17.ps1.txt`, L2-L2, offsets [56,142), `analyzed_script`, papel `exclusion_context`.

```powershell
$login = Get-Credential -Message 'Academic sign-in object; no storage or transmission'
```

`V2-D17-E02` — `datasets/safe_samples/pilot_v2/development/V2-D17.ps1.txt`, L3-L3, offsets [143,157), `analyzed_script`, papel `exclusion_context`.

```powershell
$null = $login
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Get-Credential retained locally; literal call-operator control. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D18

**ID:** V2-D18. **Particion:** development. **Familia:** V2-DEV-F09 — Credential object acquisition only.

**Forma:** construction_variant. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D18.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D18.ps1.txt). SHA-256: `83da1fe78b41bb212cfa7c0fd0373d8bb965c5eafdaca8e42cc4ad3841e0a374`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$login = Get-Credential -Message 'Academic sign-in object; no storage or transmission'
& 'Write-Output' 'The supplied object is reserved for an authorized sign-in.'
```

**Que hace / justificacion tecnica:** Solicitud legitima de objeto de autenticacion; no se guarda, extrae ni transmite material.

**Lectura de evidencia y condiciones:** Solicitud legitima de objeto de autenticacion; no se guarda, extrae ni transmite material.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Get-Credential por si solo no basta. & invoca Write-Output fijo. No operacion remota.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D18-E01` — `datasets/safe_samples/pilot_v2/development/V2-D18.ps1.txt`, L2-L2, offsets [56,142), `analyzed_script`, papel `exclusion_context`.

```powershell
$login = Get-Credential -Message 'Academic sign-in object; no storage or transmission'
```

`V2-D18-E02` — `datasets/safe_samples/pilot_v2/development/V2-D18.ps1.txt`, L3-L3, offsets [143,220), `analyzed_script`, papel `exclusion_context`.

```powershell
& 'Write-Output' 'The supplied object is reserved for an authorized sign-in.'
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Get-Credential retained locally; literal call-operator control. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D19

**ID:** V2-D19. **Particion:** development. **Familia:** V2-DEV-F10 — Displayed defense example.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D19.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D19.ps1.txt). SHA-256: `cfd3c716447a4cceb84577deb30dedbecd38bc29709a10773b1afabfea13af9c`.

```powershell
# Synthetic academic fixture. Text only: never execute.
Write-Output 'Set-MpPreference -DisableRealtimeMonitoring $true'
# The quoted command above is displayed, never invoked.
```

**Que hace / justificacion tecnica:** El cmdlet de defensa esta dentro de una cadena no evaluada.

**Lectura de evidencia y condiciones:** El cmdlet de defensa esta dentro de una cadena no evaluada.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Mostrar una orden no cambia estado. EncodedCommand solo envuelve Write-Output.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D19-E01` — `datasets/safe_samples/pilot_v2/development/V2-D19.ps1.txt`, L2-L2, offsets [56,120), `analyzed_script`, papel `exclusion_context`.

```powershell
Write-Output 'Set-MpPreference -DisableRealtimeMonitoring $true'
```

`V2-D19-E02` — `datasets/safe_samples/pilot_v2/development/V2-D19.ps1.txt`, L3-L3, offsets [121,176), `analyzed_script`, papel `exclusion_context`.

```powershell
# The quoted command above is displayed, never invoked.
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Single-quoted command example; encoded twin still only outputs data. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D20

**ID:** V2-D20. **Particion:** development. **Familia:** V2-DEV-F10 — Displayed defense example.

**Forma:** encoded_command. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D20.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D20.ps1.txt). SHA-256: `73014a4865ae05dcab04a6e42cf5ebf70a98dcfdf96b594f32efffc6d1ce0712`.

```powershell
# Synthetic academic fixture. Text only: never execute.
powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAFMAZQB0AC0ATQBwAFAAcgBlAGYAZQByAGUAbgBjAGUAIAAtAEQAaQBzAGEAYgBsAGUAUgBlAGEAbAB0AGkAbQBlAE0AbwBuAGkAdABvAHIAaQBuAGcAIAAkAHQAcgB1AGUAJwAKACMAIABUAGgAZQAgAHEAdQBvAHQAZQBkACAAYwBvAG0AbQBhAG4AZAAgAGEAYgBvAHYAZQAgAGkAcwAgAGQAaQBzAHAAbABhAHkAZQBkACwAIABuAGUAdgBlAHIAIABpAG4AdgBvAGsAZQBkAC4ACgA=
```

**Contenido decodificado completo, preparado por el equipo para revision; no se entrega al modelo en B:**

```powershell
Write-Output 'Set-MpPreference -DisableRealtimeMonitoring $true'
# The quoted command above is displayed, never invoked.
```

Procedencia: `datasets/safe_samples/pilot_v2/references/V2-D20_decoded.ps1.txt`; no es recuperacion observada de un LLM.

**Que hace / justificacion tecnica:** El cmdlet de defensa esta dentro de una cadena no evaluada.

**Lectura de evidencia y condiciones:** El cmdlet de defensa esta dentro de una cadena no evaluada.

**Comportamientos esperados propuestos:** ninguna etiqueta sustentable.

**Riesgo del escenario:** `benign`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones.

**Exclusiones:** Mostrar una orden no cambia estado. EncodedCommand solo envuelve Write-Output.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D20-E01` — `datasets/safe_samples/pilot_v2/references/V2-D20_decoded.ps1.txt`, L1-L1, offsets [0,64), `team_reference_decoded`, papel `exclusion_context`.

```powershell
Write-Output 'Set-MpPreference -DisableRealtimeMonitoring $true'
```

`V2-D20-E02` — `datasets/safe_samples/pilot_v2/references/V2-D20_decoded.ps1.txt`, L2-L2, offsets [65,120), `team_reference_decoded`, papel `exclusion_context`.

```powershell
# The quoted command above is displayed, never invoked.
```

`V2-D20-E03` — `datasets/safe_samples/pilot_v2/development/V2-D20.ps1.txt`, L2-L2, offsets [56,422), `analyzed_script`, papel `encoding_derivation_anchor`.

```powershell
powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAFMAZQB0AC0ATQBwAFAAcgBlAGYAZQByAGUAbgBjAGUAIAAtAEQAaQBzAGEAYgBsAGUAUgBlAGEAbAB0AGkAbQBlAE0AbwBuAGkAdABvAHIAaQBuAGcAIAAkAHQAcgB1AGUAJwAKACMAIABUAGgAZQAgAHEAdQBvAHQAZQBkACAAYwBvAG0AbQBhAG4AZAAgAGEAYgBvAHYAZQAgAGkAcwAgAGQAaQBzAHAAbABhAHkAZQBkACwAIABuAGUAdgBlAHIAIABpAG4AdgBvAGsAZQBkAC4ACgA=
```

**Relaciones y suficiencia propuesta por etiqueta:**

No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.


**Observaciones metodologicas:** Single-quoted command example; encoded twin still only outputs data. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D21

**ID:** V2-D21. **Particion:** development. **Familia:** V2-DEV-F11 — Runtime text evaluator.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D21.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D21.ps1.txt). SHA-256: `9daa5d778cac06663b2f2c6a24a46f9f03edac38a8d79e361f21285319aa39fa`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$runtimeCode = Read-Host 'Academic code supplied only at run time'
Invoke-Expression $runtimeCode
```

**Que hace / justificacion tecnica:** La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.

**Lectura de evidencia y condiciones:** La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.

**Comportamientos esperados propuestos:** B02.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El texto evaluado se obtiene en tiempo de ejecucion; no es posible recuperar su contenido.

**Exclusiones:** No inferir etiquetas interiores ni contenido recuperado. Sin origen remoto conocido.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D21-E01` — `datasets/safe_samples/pilot_v2/development/V2-D21.ps1.txt`, L2-L2, offsets [56,122), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$runtimeCode = Read-Host 'Academic code supplied only at run time'
```

`V2-D21-E02` — `datasets/safe_samples/pilot_v2/development/V2-D21.ps1.txt`, L3-L3, offsets [123,153), `analyzed_script`, papel `operation_or_required_context`.

```powershell
Invoke-Expression $runtimeCode
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B02`: requiere conjuntamente V2-D21-E01, V2-D21-E02; soporte propuesto `contextual`. La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.
- Relacion declarada `V2-D21-E01` -> `V2-D21-E02`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** Read-Host feeds IEX directly or through runtime Base64 conversion. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D22

**ID:** V2-D22. **Particion:** development. **Familia:** V2-DEV-F11 — Runtime text evaluator.

**Forma:** construction_variant. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D22.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt). SHA-256: `b881b6514614ad10f382a308cbe9e9acd8a0309233dbc62750b272b14d7ee768`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$runtimeBytes = Read-Host 'Academic Base64 supplied only at run time'
$runtimeCode = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($runtimeBytes))
Invoke-Expression $runtimeCode
```

**Que hace / justificacion tecnica:** La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.

**Lectura de evidencia y condiciones:** La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.

**Comportamientos esperados propuestos:** B02.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** El texto evaluado se obtiene en tiempo de ejecucion; no es posible recuperar su contenido.

**Exclusiones:** No inferir etiquetas interiores ni contenido recuperado. Sin origen remoto conocido.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D22-E01` — `datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt`, L2-L2, offsets [56,125), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$runtimeBytes = Read-Host 'Academic Base64 supplied only at run time'
```

`V2-D22-E02` — `datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt`, L3-L3, offsets [126,216), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$runtimeCode = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($runtimeBytes))
```

`V2-D22-E03` — `datasets/safe_samples/pilot_v2/development/V2-D22.ps1.txt`, L4-L4, offsets [217,247), `analyzed_script`, papel `operation_or_required_context`.

```powershell
Invoke-Expression $runtimeCode
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B02`: requiere conjuntamente V2-D22-E01, V2-D22-E02, V2-D22-E03; soporte propuesto `contextual`. La evaluacion dinamica es visible; los efectos del codigo introducido son desconocidos.
- Relacion declarada `V2-D22-E01` -> `V2-D22-E02`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.
- Relacion declarada `V2-D22-E02` -> `V2-D22-E03`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** Read-Host feeds IEX directly or through runtime Base64 conversion. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D23

**ID:** V2-D23. **Particion:** development. **Familia:** V2-DEV-F12 — Security snapshot and unknown report body.

**Forma:** original. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D23.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D23.ps1.txt). SHA-256: `8d127470dce8d1ee5211d9ec03201180037bca132e753176a488fb43ecebcb33`.

```powershell
# Synthetic academic fixture. Text only: never execute.
$defenderState = Get-MpComputerStatus
$reportBody = Read-Host 'Academic report content supplied only at run time'
Invoke-WebRequest -Uri 'https://example.invalid/academic/report' -Method Post -Body $reportBody
```

**Que hace / justificacion tecnica:** Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.

**Lectura de evidencia y condiciones:** Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.

**Comportamientos esperados propuestos:** B05, B06.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** Read-Host determina el cuerpo; no se sabe si contiene el inventario u otros datos.

**Exclusiones:** Get-MpComputerStatus solo consulta. POST no cuenta automaticamente como descarga. No inventar el contenido enviado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D23-E01` — `datasets/safe_samples/pilot_v2/development/V2-D23.ps1.txt`, L2-L2, offsets [56,93), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$defenderState = Get-MpComputerStatus
```

`V2-D23-E02` — `datasets/safe_samples/pilot_v2/development/V2-D23.ps1.txt`, L3-L3, offsets [94,169), `analyzed_script`, papel `operation_or_required_context`.

```powershell
$reportBody = Read-Host 'Academic report content supplied only at run time'
```

`V2-D23-E03` — `datasets/safe_samples/pilot_v2/development/V2-D23.ps1.txt`, L4-L4, offsets [170,265), `analyzed_script`, papel `operation_or_required_context`.

```powershell
Invoke-WebRequest -Uri 'https://example.invalid/academic/report' -Method Post -Body $reportBody
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B05`: requiere conjuntamente V2-D23-E01; soporte propuesto `individual`. Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.
- `B06`: requiere conjuntamente V2-D23-E02, V2-D23-E03; soporte propuesto `contextual`. Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.
- Relacion declarada `V2-D23-E02` -> `V2-D23-E03`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** Security query plus WebRequest POST of runtime text. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.

## V2-D24

**ID:** V2-D24. **Particion:** development. **Familia:** V2-DEV-F12 — Security snapshot and unknown report body.

**Forma:** encoded_command. **Tipo para metricas:** determinable; exact match aplicable.

**Fuente completa:** [V2-D24.ps1.txt](../datasets/safe_samples/pilot_v2/development/V2-D24.ps1.txt). SHA-256: `fcc413ff3cd3860d877235e7b53c9cc102ec2ff127ce3ebe797f80153f1b7edb`.

```powershell
# Synthetic academic fixture. Text only: never execute.
powershell.exe -NoProfile -EncodedCommand JABkAGUAZgBlAG4AZABlAHIAUwB0AGEAdABlACAAPQAgAEcAZQB0AC0ATQBwAEMAbwBtAHAAdQB0AGUAcgBTAHQAYQB0AHUAcwAKACQAcgBlAHAAbwByAHQAQgBvAGQAeQAgAD0AIABSAGUAYQBkAC0ASABvAHMAdAAgACcAQQBjAGEAZABlAG0AaQBjACAAcgBlAHAAbwByAHQAIABjAG8AbgB0AGUAbgB0ACAAcwB1AHAAcABsAGkAZQBkACAAbwBuAGwAeQAgAGEAdAAgAHIAdQBuACAAdABpAG0AZQAnAAoASQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAALQBVAHIAaQAgACcAaAB0AHQAcABzADoALwAvAGUAeABhAG0AcABsAGUALgBpAG4AdgBhAGwAaQBkAC8AYQBjAGEAZABlAG0AaQBjAC8AcgBlAHAAbwByAHQAJwAgAC0ATQBlAHQAaABvAGQAIABQAG8AcwB0ACAALQBCAG8AZAB5ACAAJAByAGUAcABvAHIAdABCAG8AZAB5AAoA
```

**Contenido decodificado completo, preparado por el equipo para revision; no se entrega al modelo en B:**

```powershell
$defenderState = Get-MpComputerStatus
$reportBody = Read-Host 'Academic report content supplied only at run time'
Invoke-WebRequest -Uri 'https://example.invalid/academic/report' -Method Post -Body $reportBody
```

Procedencia: `datasets/safe_samples/pilot_v2/references/V2-D24_decoded.ps1.txt`; no es recuperacion observada de un LLM.

**Que hace / justificacion tecnica:** Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.

**Lectura de evidencia y condiciones:** Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.

**Comportamientos esperados propuestos:** B05, B06.

**Riesgo del escenario:** `unknown`, por diseno sintetico; no es malware confirmado ni un efecto observado.

**Incertidumbre:** Read-Host determina el cuerpo; no se sabe si contiene el inventario u otros datos.

**Exclusiones:** Get-MpComputerStatus solo consulta. POST no cuenta automaticamente como descarga. No inventar el contenido enviado.

**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**

`V2-D24-E01` — `datasets/safe_samples/pilot_v2/references/V2-D24_decoded.ps1.txt`, L1-L1, offsets [0,37), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
$defenderState = Get-MpComputerStatus
```

`V2-D24-E02` — `datasets/safe_samples/pilot_v2/references/V2-D24_decoded.ps1.txt`, L2-L2, offsets [38,113), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
$reportBody = Read-Host 'Academic report content supplied only at run time'
```

`V2-D24-E03` — `datasets/safe_samples/pilot_v2/references/V2-D24_decoded.ps1.txt`, L3-L3, offsets [114,209), `team_reference_decoded`, papel `operation_or_required_context`.

```powershell
Invoke-WebRequest -Uri 'https://example.invalid/academic/report' -Method Post -Body $reportBody
```

`V2-D24-E04` — `datasets/safe_samples/pilot_v2/development/V2-D24.ps1.txt`, L2-L2, offsets [56,658), `analyzed_script`, papel `encoding_derivation_anchor`.

```powershell
powershell.exe -NoProfile -EncodedCommand JABkAGUAZgBlAG4AZABlAHIAUwB0AGEAdABlACAAPQAgAEcAZQB0AC0ATQBwAEMAbwBtAHAAdQB0AGUAcgBTAHQAYQB0AHUAcwAKACQAcgBlAHAAbwByAHQAQgBvAGQAeQAgAD0AIABSAGUAYQBkAC0ASABvAHMAdAAgACcAQQBjAGEAZABlAG0AaQBjACAAcgBlAHAAbwByAHQAIABjAG8AbgB0AGUAbgB0ACAAcwB1AHAAcABsAGkAZQBkACAAbwBuAGwAeQAgAGEAdAAgAHIAdQBuACAAdABpAG0AZQAnAAoASQBuAHYAbwBrAGUALQBXAGUAYgBSAGUAcQB1AGUAcwB0ACAALQBVAHIAaQAgACcAaAB0AHQAcABzADoALwAvAGUAeABhAG0AcABsAGUALgBpAG4AdgBhAGwAaQBkAC8AYQBjAGEAZABlAG0AaQBjAC8AcgBlAHAAbwByAHQAJwAgAC0ATQBlAHQAaABvAGQAIABQAG8AcwB0ACAALQBCAG8AZAB5ACAAJAByAGUAcABvAHIAdABCAG8AZAB5AAoA
```

**Relaciones y suficiencia propuesta por etiqueta:**

- `B05`: requiere conjuntamente V2-D24-E01; soporte propuesto `individual`. Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.
- `B06`: requiere conjuntamente V2-D24-E02, V2-D24-E03; soporte propuesto `contextual`. Consulta de defensa y envio explicito son visibles; el cuerpo no se conoce.
- Relacion declarada `V2-D24-E02` -> `V2-D24-E03`: `declared_local_binding_used_by_operation`; pendiente de validar semanticamente.

**Observaciones metodologicas:** Security query plus WebRequest POST of runtime text. La otra forma queda en esta misma familia/split; equivalencia pendiente humana.

**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.

- [ ] Etiquetas y exclusiones.
- [ ] Evidencias y relaciones suficientes.
- [ ] Riesgo y supuestos del escenario.
- [ ] Incertidumbre e inyeccion.
- [ ] Familia y forma equivalente propuesta.
