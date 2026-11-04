# Entrega — adopción exploratoria de Qwen14 e integración del prototipo

**Decisión registrada y aplicada:** `qwen2.5-coder:14b` es el modelo local experimental de B/C. La búsqueda de candidatos queda cerrada por ahora. La adopción se basa en viabilidad operativa; no acredita superioridad semántica, detector confiable, selección científica ni H1/H2.

## Decisión y fuentes

- [Registro de decisión del responsable](decisions/qwen14_exploratory_adoption.md), ID `Q14-EXPLORATORY-2026-11-03`.
- [Registro estructurado](../artifacts/qwen14_exploratory_adoption/decision.json), vinculado al hash de la instrucción del responsable.
- [Comparación exploratoria A/B/C](qwen14_exploratory_abc.md): seis scripts de desarrollo, seis A nuevos y ocho B/C históricos, sin nueva inferencia.
- [Guía de uso del prototipo](prototype_exploratory.md).

## Integración realizada

El arranque estándar `app.main:app` utiliza ahora [PrototypeAdapter y PrototypeSettings](../backend/app/services/llm/qwen14_prototype.py), a través de la [factoría FastAPI](../backend/app/api/application.py). Reutiliza el adaptador Qwen14, `AnalysisService`, motor A, política, contratos, validación de evidencia, monitor y bloqueo existentes. No se reconstruyó la arquitectura ni se modificaron reglas de la taxonomía.

Modelo/digest fijados, parámetros iniciales iguales al diagnóstico y sin fallback. Una configuración antigua para Qwen3.5, Gemma, Gemini u otro digest falla explícitamente; no se sustituye por un candidato alternativo. Los timeouts de consulta son cortos y el despacho de generación requiere el marcador de análisis propiedad del proceso. No hay cargas de prueba, descarga, cambio de proveedor ni generación durante el arranque.

A sigue funcionando sin Ollama y no consulta al LLM. B recibe únicamente el original; C recibe ese mismo texto más recuperación 1A verificada. Ambos comparten política y parámetros. No reciben etiquetas de referencia/1B ni respuestas anteriores de B.

La interfaz conserva su diseño y contrato de resultados. Se actualizaron las referencias al modelo y los avisos funcionales: predicciones experimentales B/C, soporte semántico pendiente, citas literales verificadas e indeterminación/alcance parcial. Los resultados rechazados siguen sin publicar etiquetas, riesgo o evidencias aceptadas; su texto crudo se muestra escapado y separado para diagnóstico. Las salidas antiguas conservan el nombre de modelo realmente registrado, sin renombrarlas a Qwen14.

## Estado funcional comprobado

El prototipo compila y sirve el frontend de producción desde la API. Se verificó React → HTTP FastAPI → A determinista con el proveedor LLM expresamente simulado como desconectado. El servidor temporal se cerró tras la prueba; no se dejó un servicio nuevo ejecutándose.

Los endpoints existentes permanecen: salud, metadatos, capacidades, estado, análisis A/B/C y comparación. Los metadatos del perfil seleccionado indican adopción exploratoria, ausencia de fallback, ocho adjudicaciones pendientes y H1/H2 no establecidas. A arranca como modo inicial; montar React, seleccionar una configuración o consultar estado no despacha B/C.

La generación real de Qwen14 después de integrar el arranque **no se probó en este encargo**, por la instrucción de cero inferencias nuevas. Su compatibilidad real previa pertenece al diagnóstico de ocho intentos y se mantiene identificada como histórica. B/C actuales se verificaron con mocks del transporte; no se simulan éxitos empíricos adicionales.

## Regresiones

| Verificación | Resultado |
|---|---:|
| Backend completo | **1.068 aprobadas** |
| Frontend, tres archivos | **29 aprobadas** |
| Integración React/API HTTP usando A | **1 aprobada** |
| Compilación TypeScript + Vite | **Correcta** |
| Regresión específica de históricos/comparador | **43 aprobadas**; incluidas también en el pase completo |

La advertencia restante es una deprecación de Starlette/httpx del entorno; no produjo fallos. Evidencia: [backend completo](../artifacts/qwen14_exploratory_adoption/backend_regressions_final.xml), [históricos](../artifacts/qwen14_exploratory_adoption/historical_regressions.xml), [frontend/HTTP/build](../artifacts/qwen14_exploratory_adoption/frontend_validation.json).

Las pruebas cubren selección/digest explícitos, rechazo de configuración antigua, A independiente con proveedor desconectado, estado sin generación, B/C equivalentes y sin filtrado de referencias, memoria insuficiente, ausencia de Ollama, procedencia rechazada sin hallazgos publicados, timeouts y propiedad del despacho, límite del diagnóstico histórico y uniones/hash del comparador. También conservan los controles existentes de ejecución, inyección como datos, contratos y seguridad del frontend.

El primer pase completo detectó que las pruebas históricas Gemma copiaban el archivo API actual aunque el congelado exigía su versión anterior. Se adaptó exclusivamente esa preparación de prueba: para ese archivo evolucionado se usa la copia histórica y se exige **el mismo SHA-256 original**. No se cambiaron el congelado, los controles del protocolo, las respuestas o los umbrales, ni se omitieron pruebas. Las nuevas pruebas de aplicación ejercitan el arranque actual; las históricas conservan su versión exacta. El pase completo final es satisfactorio.

## Comparación y límites

La primera pareja mejora parcialmente con C: elimina B02 injustificado, reconoce B05 y usa recuperación correcta, pero sigue omitiendo B06. La segunda pareja no mejora clasificación; ambos informes se rechazan, y C empeora la procedencia de citas. No se supone superioridad universal de C.

A produce tres resultados completos y tres parciales. Sus coincidencias de etiquetas se describen junto con esa cobertura: el bloque invocado es un FN por sintaxis no implementada. Los conjuntos vacíos parciales no se presentan como negativos benignos. B tiene errores de credenciales, activación y reconstrucción; C muestra tanto ayuda parcial como deterioro. El [informe comparativo](qwen14_exploratory_abc.md) contiene resultados por unidad, aceptados/rechazados, FP/FN, denominadores y observaciones.

El material es desarrollo ya expuesto: seis textos y dos parejas, con referencias reutilizadas y observaciones semánticas asistidas por IA. **Las ocho adjudicaciones personales Qwen14 siguen pendientes**, además de los pendientes históricos de Gemma. No se inventó ninguna revisión personal ni se declararon confirmadas/refutadas H1/H2.

## Preservación y presupuestos

La [verificación final](../artifacts/qwen14_exploratory_adoption/integrity_final.json) comprobó 9.285 archivos preexistentes: **9.047 archivos históricos de artefactos, experimentos y documentación sin cambios**; doce modificaciones intencionales de integración, textos y pruebas, y el resto intacto. Se conservaron las 79 entradas del congelado Qwen14 con sus hashes originales en el [archivo de fuentes](../artifacts/qwen14_exploratory_adoption/source_archive_manifest.json).

- Inferencias reales nuevas Qwen14: **0**. Ledger diagnóstico: **8/8**, hash intacto.
- Solicitudes Gemini nuevas: **0**. Ledger global: **5/12**, SHA-256 `dd2a7f346118155de25e68f1ab2ded45bc28dfbffa722b7c25e529d8ef75d60b`, intacto.
- Qwen14 y Qwen 7B conservados con sus identificadores/digests; ningún modelo descargado o eliminado. [Inventario consultado](../artifacts/qwen14_exploratory_adoption/ollama_inventory_readonly.json).
- Sin ejecución de scripts, recuperaciones o contenido generado; sin consultas a URLs de muestras ni bóvedas.
- Rama `develop`, sin staging ni operaciones Git de escritura. Índice, HEAD y referencia de rama intactos.
- Evaluación independiente y Fase 4: **no iniciadas**.

El código vivo de la API evolucionó; por ello no se afirma que su hash siga igual al congelado de una campaña cerrada. La copia exacta y el manifiesto permiten verificar el código histórico sin reescribirlo ni eludir el cierre de su controlador. No se modificó el informe diagnóstico anterior para presentar la adopción como aprobación retrospectiva.

## Trabajo mínimo pendiente

1. Revisar personalmente las ocho fichas, con soporte semántico, procedencia, activación, reconstrucción, riesgo e incertidumbre; registrar eventos nuevos por hash.
2. Cerrar la documentación y demostración del prototipo con los límites actuales, conservando advertencias, exportación y estados de indisponibilidad. No usarlo para decisiones reales de seguridad sin revisión humana.
3. Preparar la evaluación independiente posterior: familias no vistas, referencias revisadas antes de salidas, configuración y criterios congelados y autorización de presupuesto. H1 debe contrastar clasificación pareada; H2 requiere adjudicar afirmaciones no respaldadas, separadas de literalidad.
4. Ejecutar esa evaluación solo tras autorización posterior, conservando resultados negativos y rechazos. No buscar otro modelo ni ajustar los objetivos para forzar un resultado favorable.

La elección técnica está cerrada y el prototipo integra el modelo adoptado. La validación científica y las adjudicaciones personales permanecen explícitamente pendientes.
