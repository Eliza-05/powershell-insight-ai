> Copia publicable derivada de un informe historico. Rutas operativas redactadas y enlaces ajustados; no es una nueva validacion, acta humana o autorizacion. La responsabilidad vigente de Karol consta en el plan.

# PowerShell Insight AI — estado de esta continuación

**BLOQUEADO ANTES DEL FREEZE.** El despliegue técnico del nuevo SHA funciona; la preparación científica no se completó y la revisión humana sigue pendiente.

## Resultado técnico

SHA local y remoto: `7fc29f86d50298207a2a480ac3989be175ec9cb1`, rama `integration/final-validation`, árbol limpio. Coincide exactamente con el contenido de los cinco archivos revisados; no se hicieron operaciones Git de escritura.

Nueva copia: `<COPIA_AISLADA>`. Entorno propio Python 3.13.18, dependencias fijadas y pip check correcto. **767 pruebas nativas aprobadas**, sin F4 y con acceso al Ollama real bloqueado durante los tests. Preflight final: **PREFLIGHT APROBADO CON OBSERVACIONES**.

El binding verifica montaje, dispositivo, capacidad y espacio libre actual mediante el ancestro accesible, sin sudo ni cambios de OLLAMA_MODELS. El SHA-256 real de la evidencia coincide con el declarado. La ruta canónica protegida procede de la captura autorizada anterior y no se vuelve a resolver en vivo: es una limitación expresa. La admisión de RAM no garantiza una inferencia exitosa.

Se verificaron 180 archivos transferidos y la integridad de la recuperación. Git exportó 136 con CRLF por core.autocrlf=true; se verificó que no hay diferencias adicionales respecto del commit. Véase [procedencia y ambos hashes](../integracion/PROCEDENCIA_EXPORTACION_GIT.md).

## Bloqueo científico observado

Se ejecutó la preparación prospectiva una sola vez. Guardó las 16 referencias authored y una solicitud B; la primera C fue rechazada por `proposal_context_budget_exceeded`. No hay configuración, orden o manifiesto completos del controlador. No se repitió prepare ni se ajustó código, política, parámetros o casos usando F4.

La guarda vigente compara bytes UTF-8 de los mensajes, más 512 de reserva y 2048 de salida, con contexto 8192: presupuesto conjunto de mensajes 5632 bytes. La política ocupa 3241 bytes. La parada **no fue una inferencia fallida ni una medición del tokenizer o de la capacidad real del modelo**.

El responsable confirmó que la revisión humana está pendiente. Se prepararon las [16 fichas y las plantillas](../../EVIDENCIAS.md#material-restringido), con 0 aprobaciones y originales cuyo SHA-256 coincide con el registro anterior. Son propuestas documentales de IA; no sustituyen una revisión humana ni habilitan Proposal.seal.

El [informe completo de las 16 comprobaciones](INFORME_PUERTA_PROVISIONAL.PUBLICABLE.md) y el [protocolo Qwen3 provisional](../evaluacion/PROTOCOLO_QWEN3_PROVISIONAL.PUBLICABLE.md) explican predicciones originales/aceptadas, H1/H2, rechazos, timeouts, faltantes, indeterminados y denominadores. Los documentos Qwen14 se conservaron como antecedentes; no validan Qwen3.

## Estado experimental y evidencias

| Concepto | Estado |
|---|---|
| FREEZE definitivo | No creado |
| Llamadas autorizadas / intentadas / exitosas / fallidas | 0 / 0 / 0 / 0 |
| Presupuesto previsto aún sin autorizar | 32 |
| Resultados científicos A/B/C | No ejecutados |
| H1 / H2 | No evaluadas; métricas no medidas |
| Ledger científico real | No creado |
| Campaña activa | Ninguna observada |
| Históricos y despliegue anterior | 2.765 hashes conocidos sin cambios, dentro del alcance documentado |
| EC2 | Encendida; no se apagó |

Se recuperaron el paquete humano, los logs/XML y la preparación parcial cruda en `recovered/`, separados de los históricos. Tres archivos de transferencia coinciden con sus hashes remotos; 40 archivos del paquete y cuatro de la preparación parcial quedaron verificados. Los originales AWS se conservan. El manifiesto **parcial** tiene SHA-256 `41028c708d628ed37c9841bd50bcdc6a80fa5c86eb477bba2e3cb042e4acdba3` y declara explícitamente que no es un candidato completo compatible con el controlador.

## Decisión necesaria

No procede aprobar el FREEZE o las inferencias de este candidato. Hace falta la revisión humana y una decisión metodológica sobre la inviabilidad de preparación bajo el contrato vigente. Si se abre un diseño revisado, deberá registrarse la exposición de estas entradas y valorar una reserva independiente; no se deben utilizar los mismos casos para ajustar una solución y después presentarlos como evaluación virgen.

Recomendación: mantener la rama sin merge científico a develop mientras se resuelve ese punto. La entrega académica puede documentar el prototipo funcional y las pruebas técnicas, con el bloqueo y la evaluación pendiente expresamente declarados.

**BLOQUEADO ANTES DEL FREEZE.**
