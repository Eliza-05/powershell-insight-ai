# Guía de demostración — PowerShell Insight AI

**Entorno:** VM de Google Cloud `psi-cierre` (proyecto `psi-cierre`, us-central1-c).
**Datos:** solo fixtures sintéticos de desarrollo, nunca F4.
**Estado de esta guía:** ver la sección 8. La demo con el modelo real necesita una autorización propia, separada de la campaña F4, y nunca se hace a la vez que la campaña.

## 1. Requisitos

- Acceso a la consola de Google Cloud del proyecto `psi-cierre`.
- La clave SSH autorizada en la VM. La parte pública está en la metadata de la instancia; la privada no se comparte por chat.
- Un PC con `ssh` y un navegador. No hace falta Node ni Python en el PC: el frontend ya va compilado.

## 2. Encender la VM y obtener la IP

1. En la consola, **Compute Engine → Instancias de VM**, marca `psi-cierre` y pulsa **Iniciar/Reanudar**.
2. Copia la **IP externa**. Cambia cada vez que la VM se apaga y se enciende, porque no es estática.

## 3. Conectarse y comprobar el servicio (sin generar texto)

```sh
ssh -i <clave_privada> psi@<IP>
systemctl is-active ollama
ss -ltn | grep 11434              # debe mostrar solo 127.0.0.1:11434
curl -s 127.0.0.1:11434/api/tags  # qwen3-coder:30b con digest 06c1097e…
cat /proc/sys/vm/overcommit_memory  # 0
free -g; df -h /
```

## 4. Arrancar la aplicación en loopback

Usa la copia desplegada del SHA final (`~/psi-final-<sha>`), que trae el frontend compilado en `frontend/dist`.

```sh
cd ~/psi-final-<sha>
export PSI_LLM_PROFILE=qwen3coder-v2
export PYTHONPATH="$PWD/backend:$PWD"
.venv/bin/python -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

## 5. Túnel desde el PC y navegador

En otra terminal del PC (el puerto 8000 local debe estar libre):

```sh
ssh -N -L 8000:127.0.0.1:8000 -i <clave_privada> psi@<IP>
```

- Abre `http://127.0.0.1:8000` en el navegador.
- Comprobaciones sin generación: `/api/health`, `/api/capabilities` (deben aparecer `qwen3-coder:30b`, el digest y la estrategia `v2-deterministic-layers-2`) y `/api/provider/status`.
- El navegador nunca accede al puerto 11434; solo habla con el backend por el túnel.

## 6. Recorrido de la demo

1. **Modo A:** pega un script sintético de desarrollo, por ejemplo uno de `datasets/safe_samples/pilot_v2/development/`, y analiza. No usa el LLM. Muestra la desofuscación 1A y las reglas 1B.
2. **Modo B / C / comparar (requiere autorización):** con el mismo texto sintético, cada análisis B o C es **una** llamada al modelo; "Comparar" hace dos. En CPU, cada una tarda de 1 a 5 minutos (hay un plazo de 300 s).
   - Muestra las etiquetas publicadas, las citas validadas, el riesgo del modelo y la sección del verificador (`operational.evidence_check`), donde se ve qué etiquetas descartó.
   - Muestra también el aviso de la capa de comentarios.
3. **Exportar:** descarga el JSON del resultado desde la interfaz.
4. **Errores ensayados:**
   - Entrada vacía: `empty_input`.
   - Texto por encima del límite: `input_too_large`.
   - Dos análisis LLM simultáneos: `analysis_busy`, sin reintento automático.
5. **Límites que hay que explicar:**
   - Las citas literales no certifican soporte semántico.
   - La capa de comentarios no protege de instrucciones dentro de cadenas.
   - El verificador solo descarta etiquetas, nunca las añade.
   - El modelo no pasó el gate científico de selección; ver `RESULTADOS_H1_H2.md` para Fase 4.

## 7. Parar todo

1. En la VM, Ctrl+C en uvicorn. En el PC, Ctrl+C en el túnel.
2. Comprueba que no hay campañas ni transferencias en curso: `pgrep -fa experiments.phase4` debe salir vacío.
3. Con autorización de la responsable, **detén la VM** en la consola (Detener). Detenida solo cobra el disco.

## 8. Verificación de esta guía (10 nov 2026, VM n2-custom-12, SHA `4133033`, frontend compilado `9ff68d9c…`)

| Paso | Resultado |
|---|---|
| 2. Encender la VM y obtener la IP | Hecho desde la consola de GCP. La IP cambió entre arranques (`35.224.28.89` → `34.45.175.64`), lo que confirma la advertencia |
| 3. Comprobaciones del servicio | Ollama activo solo en 127.0.0.1, digest correcto, `overcommit_memory = 0` |
| 4. App en loopback con el perfil explícito | `uvicorn app.main:app` en 127.0.0.1:8000. `/api/health` OK; `/api/capabilities` muestra `qwen3-coder:30b`, el digest, `timeout_seconds 300`, `fallback_enabled false` y la estrategia `v2-deterministic-layers-2`; `/api/provider/status`: `available` y `ready_for_inference` en true; `/` (frontend) devuelve 200 |
| 6.1 Modo A | D02 de desarrollo: `partial` (cobertura parcial de 1A/1B), sin etiquetas deterministas |
| 6.2 Comparar (A+B+C) con el modelo real, autorizado ("Autorizo 2 llamadas de demo con un script sintético de desarrollo", 14:10) | Exactamente **2 llamadas**. **B:** `completed`, 76 s; el modelo propuso **B01** (correcto según la referencia de desarrollo de D02), el verificador lo **descartó** y no se publicó ninguna etiqueta; riesgo del modelo `suspicious`. **C:** `invalid_response` (49 s). Resultado guardado en `compare_D02.json` (sha256 `38389238…`, restringido) |
| 6.4 Errores | Entrada vacía → `empty_input`; 70 000 bytes → HTTP 413; segunda solicitud LLM durante Comparar → `analysis_busy` (409, sin despachar ni reintentar) |
| 6.3 Exportar | La respuesta JSON de la API es el mismo objeto que descarga la interfaz. La descarga desde el navegador está verificada con las pruebas E2E sintéticas (`integrated.mjs`: 6 descargas) |
| 5. Túnel y recorrido visual en vivo | No reproducido en esta sesión: la automatización no tiene un navegador en el PC conectado al túnel. Lo hace Karol con los pasos 5–6. La interfaz está validada con E2E en el navegador (`VALIDACION_FRONTEND_SINTETICA.json`) |
| 7. Parada | uvicorn detenido; sin procesos de campaña. La VM **sigue encendida** hasta que Karol autorice detenerla |

**Observación para la demo:** el caso B de arriba muestra en pequeño el hallazgo de Fase 4. El modelo acertó la etiqueta y el verificador conservador la descartó. Conviene explicarlo así en la presentación.
