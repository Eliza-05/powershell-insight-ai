# Pendientes metodológicos antes de la Fase 4

> **Estado vigente, 2026-11-02: ESTADO C — NO APTO PARA AVANZAR con el modelo/configuración
> actuales.** El [cierre integral](pre_phase4_model_readiness.md) resuelve el cierre
> metodológico del piloto, pero no aprueba el modelo. Las notas siguientes conservan
> los pendientes tal como se registraron antes de Fase 3; su disposición actual se añade abajo.

Registrados **antes de implementar la aplicación de Fase 3**, por instrucción expresa
del responsable (2026-11-02). No bloquean el desarrollo del producto bajo DEV-03.

1. Cierre metodológico del piloto v2 interrumpido: conservar 58 intentos y 68 llamadas
   de selección pendientes, sin reintentos ocultos ni alteración de sus artefactos.
2. Selección definitiva del modelo: Qwen3.5 continúa provisional; una UI funcional no
   constituye aprobación de calidad.
3. Resolución del incidente de memoria para campañas largas, con márgenes de RAM y
   compromiso estables y presupuesto operativo registrado.
4. Evaluación científica independiente A/B/C, con familias y particiones ajenas a los
   ejemplos de desarrollo y a las comprobaciones funcionales de la aplicación.
5. Adjudicación semántica humana de la calidad del LLM: citas literales y JSON válido
   no prueban soporte de una conclusión. Mantener los defectos registrados de Fase 2.
6. Confirmación experimental o rechazo de H1/H2; actualmente no demostradas.
7. Congelación definitiva de dataset, criterios, prompt, parámetros y entorno de evaluación
   antes de iniciar la campaña independiente, con hashes y decisiones registradas.

Esta fase no ejecuta campañas, reabre selección, modifica umbrales ni adjudica resultados
del piloto. Referencias: [cierre de Fase 2](phase2_closure.md),
[decisión DEV-03](phase2_integration.md), [roadmap](roadmap.md).

## Disposición actual de los pendientes

| Pendiente original | Cierre del 2026-11-02 |
|---|---|
| Cierre metodológico piloto v2 | **Resuelto:** cerrado sin aprobación, máximo 71/72 frente a 100%. Conservar 58 intentos y 68 llamadas sin ejecutar; no reanudar para perseguir un pase imposible |
| Selección definitiva | Abierta: P0/P1/P2/P3 diagnosticados, sin configuración aprobada; no se recomienda gastar 72 con estos perfiles |
| Memoria/campaña extensa | Bloqueo inicial superado para 24 llamadas seguras; mínimos RAM/compromiso 6,641/9,839 GiB, sin OOM/timeout/cancelación. Campaña extensa no demostrada |
| Evaluación independiente A/B/C | No iniciada; exige modelo seleccionado y datos/familias independientes |
| Adjudicación semántica humana | 54 fichas previas +24 nuevas =78; 0 decisiones humanas. Literalidad no certifica soporte |
| H1/H2 | Sin confirmar/rechazar mediante evaluación final |
| Congelación definitiva | Pendiente; no reutilizar resultados observados como nueva reserva |

P2-LLM-01/02/03 y P2-REAL-01 siguen abiertos como calidad del modelo. Se conservan
sus evidencias. Las 24 llamadas de desarrollo terminaron: 14 aceptadas por contrato/citas,
10 rechazadas, 0 indeterminadas; presupuesto restante 0. C-P3 sí terminó, truncado a 3072
tokens sin respuesta final. C quedó 0/3 aceptado en P0/P1/P3; no se repitió ninguna llamada.
Las correcciones tienen pruebas sin ocultar falsos positivos. El [artefacto terminal](../artifacts/pre_phase4/pilot_v2_terminal.json)
actualiza estado sin sobrescribir el acta anterior.

Diagnóstico autorizado completado; [comparación y crudos](../artifacts/pre_phase4/resume_01/results.md).
Pasos mínimos: revisión de las fichas y decisión de detener estos perfiles o justificar
otro candidato/intervención con presupuesto nuevo. Solo si se justifica, reserva nueva y autorización
separada de selección (24×3=72 llamadas), adjudicación y cumplimiento íntegro antes de
congelar evaluación final. Ninguna nueva selección, cambio de modelo ni A/B/C final
está autorizada por este cierre. DEV-03 sigue permitiendo desarrollo de producto provisional.
