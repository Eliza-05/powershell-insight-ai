# Prototipo local con Qwen14 experimental

El arranque estándar `app.main:app` selecciona explícitamente **Qwen2.5-Coder 14B** para B/C. La [decisión de alcance](decisions/qwen14_exploratory_adoption.md) cierra la elección del modelo por viabilidad operativa. El LLM tiene calidad diagnóstica baja y sus ocho respuestas siguen pendientes de revisión personal. H1/H2 y la selección científica no están aprobadas.

## Arranque

Desde la raíz, con las dependencias ya preparadas:

```powershell
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe -B -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --no-access-log
```

Abrir `http://127.0.0.1:8000`. Para desarrollar con Vite, iniciar también `npm.cmd --prefix frontend run dev` y abrir el puerto 5173. Ambos usan el mismo contrato `/api`.

El arranque, las consultas de salud/capacidades/estado y seleccionar un modo **no generan inferencias**. A está seleccionado inicialmente y funciona sin Ollama. B/C y comparar A/B/C requieren una acción explícita de análisis; comparar implica dos solicitudes LLM. En este encargo no se pulsaron esas acciones contra un modelo real: las pruebas B/C usan mocks y la comparación documental reutiliza respuestas existentes. La adopción no amplía el presupuesto diagnóstico cerrado ni autoriza una campaña futura.

## Perfil y controles

El modelo y digest están fijados en `backend/app/services/llm/qwen14_prototype.py`. No hay fallback, descarga, actualización de Ollama, carga de prueba ni cambio de Windows. Se usa el adaptador Qwen14 existente y los mismos servicios A/B/C, política y validador.

CPU, contexto 8192, máximo 2048 tokens, temperatura 0, semilla 42, diez hilos, batch 256, keep-alive 5 minutos y plazo absoluto 300 s. `think` y `draft_num_predict` se omiten de la solicitud. B/C usan una misma instancia de configuración. El estado es de solo lectura, con timeout corto; no fuerza la carga del modelo.

`PSI_PIPELINE_SETTINGS` es opcional y debe apuntar a JSON compatible con `PrototypeSettings`. No se carga `.env` automáticamente. Sin esa variable se usa Qwen14; un JSON antiguo para otro modelo/digest o puerto falla explícitamente al arrancar, sin fallback. Los valores publicados por `/api/capabilities` describen la configuración solicitada. Antes de una evaluación futura deberá congelarse nuevamente esa configuración.

Se mantienen los umbrales del perfil Qwen14: RAM **y** compromiso disponibles de al menos 15.005.580.032 bytes en frío (13,975 GiB, incluidos 2 GiB de margen); 3 GiB con el mismo modelo/contexto residente en CPU; piso de 2 GiB durante inferencia. Si Ollama está ausente, falta el modelo/digest, hay otro modelo cargado, el circuito está bloqueado o la memoria no alcanza, se informa la indisponibilidad. No se cierran aplicaciones, no se descargan modelos y no se reintenta automáticamente.

## Cómo leer las salidas

- **A:** reglas y recuperación deterministas dentro del subconjunto soportado, sin veredicto de intención o malware.
- **B:** predicciones experimentales sobre el original, sin información de 1A/1B.
- **C:** predicciones experimentales sobre original y recuperación 1A verificada, sin etiquetas de 1B ni respuestas de B.
- **Citas aceptadas:** literalidad y procedencia verificadas; el soporte semántico sigue sin adjudicar.
- **Reconstrucciones del modelo:** no verificadas e inadmisibles como evidencias.
- **Respuestas rechazadas:** sin hallazgos, riesgo o evidencias publicados; el crudo se muestra solo en diagnóstico.
- **Indeterminación/alcance parcial:** fragmentos no resueltos o limitaciones; no se convierte en un negativo benigno.

Las instrucciones dentro del script son datos no confiables. El modelo puede ignorar esta política, como muestran los resultados diagnósticos; el sistema no ofrece herramientas ni ejecuta su contenido. No se garantiza resistencia semántica a inyección. No usar las predicciones para decisiones reales de seguridad sin revisión humana.

## Investigación pendiente

La [comparación actual](qwen14_exploratory_abc.md) es desarrollo descriptivo con seis textos expuestos y ocho inferencias históricas. No sirve como conjunto independiente final. Las adjudicaciones personales de ocho respuestas Qwen14 y las de Gemma siguen pendientes en sus registros respectivos.

Para cerrar el prototipo: revisar personalmente los resultados, mantener exportación y procedencia, verificar la aplicación con mocks y documentar sus límites. Para una evaluación independiente posterior: separar familias no vistas, revisar referencias antes de salidas, congelar modelo/digest/política/parámetros/criterios, autorizar un presupuesto nuevo y registrar todos los fallos sin reintentos oportunistas. H1 compara F1 B/C sobre los mismos casos; H2 requiere adjudicar afirmaciones no respaldadas y no se sustituye por literalidad de citas. Se debe aceptar y publicar un resultado negativo. No se propone otra búsqueda de modelos.
