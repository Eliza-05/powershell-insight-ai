# Q14-EXPLORATORY-2026-11-03 — adopción exploratoria local

**Decisión adoptada por el responsable el 3 de noviembre de 2026, America/Bogota.** Se cierra la búsqueda de modelos por ahora. `qwen2.5-coder:14b` queda seleccionado exclusivamente como modelo local experimental para B y C de PowerShell Insight AI.

La [instrucción del responsable](../../artifacts/qwen14_exploratory_adoption/owner_decision.txt) acepta expresamente los límites del diagnóstico: 6/8 informes utilizables, 1/8 conjuntos exactos, precisión 0,40, recall 0,3333 y F1 micro 0,3636, incluidos errores de clasificación, reconstrucción y procedencia. El [informe diagnóstico](../qwen25_coder14b_final_viability.md) y sus datos permanecen como resultados históricos, sin modificar criterios, etiquetas, respuestas ni métricas.

La decisión se basa en **viabilidad operativa y posibilidad de estudiar los errores**, no en superioridad semántica demostrada. No constituye aprobación de selección científica, certificación del detector, confirmación de H1/H2 ni autorización de uso para decisiones reales de seguridad sin revisión humana. Las adjudicaciones personales de las ocho respuestas siguen pendientes; las observaciones de IA no las sustituyen.

El prototipo mantiene A determinista, B sobre el original y C sobre ese mismo original más recuperación verificada de 1A. B/C comparten modelo, digest, política y parámetros; no reciben etiquetas de referencia, decisiones de 1B ni respuestas previas. No existe fallback a Qwen3.5, Gemma, Gemini u otro modelo. Nunca se ejecutan muestras, recuperaciones o contenido generado.

Modelo fijado: Qwen2.5-Coder 14B, Q4_K_M, digest `9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`. Perfil inicial equivalente al diagnóstico: CPU, contexto 8192, salida 2048, temperatura 0, semilla 42, diez hilos y plazo 300 s. Sin parámetro de razonamiento interno ni herramientas.

**Este encargo autoriza cero inferencias nuevas.** La integración se verifica con mocks; la comparación usa seis ejecuciones A estáticas nuevas y ocho respuestas B/C históricas identificadas como reutilizadas. El ledger diagnóstico permanece agotado en 8/8 y Gemini en 5/12. No se descargan modelos, no se eliminan Qwen14/7B, no se inicia evaluación independiente ni Fase 4 y no se realizan operaciones Git de escritura.

La interfaz debe separar resultados deterministas, predicciones experimentales, literalidad verificada, soporte semántico no adjudicado, rechazos e indeterminación. La ausencia de etiquetas no es una prueba de benignidad y una cita literal no valida automáticamente una clasificación.

Antes de cambiar el arranque se preservaron las 79 entradas del congelado diagnóstico en un [archivo de fuentes y entradas](../../artifacts/qwen14_exploratory_adoption/source_archive_manifest.json). El congelado original no se reescribe: el código de aplicación puede evolucionar, y la verificación histórica usa esas copias exactas. No se vuelve a ejecutar el controlador cerrado para eludir su límite.

Estado de entrega e instrucciones: [prototipo exploratorio](../prototype_exploratory.md). Comparación de desarrollo: [A/B/C con resultados existentes](../qwen14_exploratory_abc.md). Evaluación independiente e H1/H2: pendientes de casos no vistos, referencias revisadas, diseño congelado y autorización posterior de presupuesto.
