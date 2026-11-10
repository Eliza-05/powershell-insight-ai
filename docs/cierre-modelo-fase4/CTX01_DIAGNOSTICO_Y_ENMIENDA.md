# CTX-01: diagnóstico y enmienda del presupuesto de contexto

**Fecha:** 10 nov 2026, America/Bogota. **Rama:** `integration/final-validation`. **Base:** `a3ba71e`.
**Responsable de la corrección:** Claude (IA), a petición de Karol. **Aprobación requerida:** Karol, responsable designada del cierre. Ver la sección 6.

> Este diagnóstico **no usó F4**. No se abrieron `experiments/phase4/dataset.py`, la preparación parcial preservada ni el paquete de revisión. Todos los datos provienen de entradas de desarrollo y selección del piloto v2 y de fixtures sintéticos.

## 1. Síntoma

La preparación del candidato de Fase 4 en `7fc29f8` se detuvo con `proposal_context_budget_exceeded`, con 1 request B y 0 C. El mismo control existe en el adaptador (`qwen14.py`, heredado por Qwen3), así que la aplicación también rechazaba en B y C scripts medianos.

## 2. Causa raíz

Las dos guardas calculaban:

```
Σ bytes UTF-8 de los mensajes + 512 (reserva de plantilla) + 2048 (salida) ≤ 8192
```

Esto trata **cada byte como un token**. Es una cota superior válida, porque un token BPE nunca ocupa menos de un byte, pero muy holgada. Con la política v2 (3241 bytes), al JSON del usuario le quedan solo 2391 bytes, original y recuperación incluidos. No es un fallo de la medición de tokens ni prueba de que el modelo no pueda con esos casos: es una unidad equivocada usada como presupuesto.

## 3. Evidencia (solo desarrollo)

Fuente: `evidencias-publicables/ctx01/CALIBRACION_TOKENS_DESARROLLO.json` (sha256 `f846d7e7…`). Son 207 llamadas reales a `qwen3-coder:30b` (Ollama 0.40.14, EC2 CPU) del laboratorio, rondas R3–R7: casos del piloto v2 de desarrollo y selección y fixtures de humo, con 60 entradas distintas. En cada una se compara `prompt_eval_count`, informado por Ollama, con los bytes de los mensajes enviados.

| Medida | Valor |
|---|---|
| Tokens por byte: mín. / mediana / p95 / máx. | 0,205 / 0,218 / 0,296 / 0,323 |
| Máximo `prompt_eval_count` observado | 2202 tokens (presupuesto de entrada real: 8192 − 2048 − 512 = 5632) |
| Llamadas que la regla de bytes habría rechazado | **15 de 207**, aunque ninguna usó más del 39 % del presupuesto |
| Llamadas rechazadas con la regla escalada 0,5 | 0 de 207 |

## 4. Corrección

1. **`context.message_token_upper_bound(messages, settings)`** es la única regla, y la usan tanto el adaptador como `prepare.py`:
   - Perfiles históricos: un token por byte (`message-bytes-v2`). Su comportamiento no cambia.
   - Perfil `qwen3coder-v2`: `ceil(bytes × 0,5)` (`message-bytes-scaled-v3`).
2. **`Qwen3CoderSettings.context_tokens_per_byte_upper_bound = 0.5`**, validado en el rango [0,5, 1,0]. Solo puede hacerse más conservador. 0,5 deja un margen de más de 1,5× sobre el peor cociente observado (0,323).
3. **Nueva comprobación posterior (solo con la cota escalada):** si los tokens reales de entrada informados por Ollama superan `num_ctx − num_predict` (6144), la respuesta **no se publica** (`context_limit`). Así se cubre el riesgo de que la estimación se quede corta y el servidor recorte la entrada.
4. **Sin cambios** en el modelo, el digest, `num_ctx=8192`, `num_predict=2048`, la reserva de plantilla de 512, el timeout, la política, la estrategia, el sanitizador o el verificador. Nunca se recorta ninguna entrada.

## 5. Pruebas

- `backend/tests/pipelines/test_context_budget_ctx01.py`, con 11 pruebas:
  - Los perfiles históricos no cambian.
  - El redondeo es hacia arriba.
  - El factor solo acepta valores más conservadores.
  - `prepare` y el adaptador usan la misma regla.
  - Una entrada que la regla de bytes rechazaba ahora se envía completa, sin recortes.
  - Una entrada mayor que la cota escalada se sigue rechazando antes del despacho.
  - Una entrada real que invade la reserva de salida no se publica.
  - Los 24 casos de desarrollo del piloto v2 caben en B y en C.
- La selección segura del plan (sección 16) da 767 aprobadas, sin regresiones, más las 11 nuevas.

## 6. Riesgos y decisión

- **Riesgo residual:** un script F4 con un cociente de tokens por byte mayor que 0,5 en el conjunto del mensaje, por ejemplo si fuera casi todo Base64 o texto aleatorio, quedaría subestimado. En ese caso:
  - Si Ollama rechaza la entrada, la llamada falla limpia (`ollama_http_error`).
  - Si la acepta con muchos tokens, la comprobación posterior la descarta (`context_limit`).
  - Nunca se publica una respuesta sobre una entrada recortada. Si ocurre, cuenta como fallo de esa unidad según la política de fallos (PROTOCOLO_FASE4 §Fallos); no se repite ni se ajusta.
- **Independencia:** el factor 0,5 se fijó solo con datos de desarrollo y selección, antes de cualquier preparación nueva con F4. Si al preparar el candidato algún caso F4 sigue excediendo la cota, **no se cambia el factor**: se documenta como impedimento de esa unidad.
- **Decisión de la responsable: APROBADA.** Karol, responsable designada del cierre, 2026-11-10 09:47 America/Bogota, en el chat de trabajo: *"apruebo la enmienda"*. Respondía a la propuesta textual "Apruebo la enmienda CTX-01 (factor 0,5 tokens/byte para qwen3coder-v2)". Aprueba el método y el factor descritos en este documento. No aprueba referencias, FREEZE ni inferencias.
