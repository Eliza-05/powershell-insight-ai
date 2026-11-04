# Fase 4 — referencias propuestas de los 16 textos

**Pendientes de revisión personal y de congelación aprobada. Cero inferencias nuevas.**
No se usaron predicciones B/C ni etiquetas 1B para construir estas propuestas. Los resultados 1A verifican recuperación textual, no las referencias semánticas.

| ID | Escenario | Referencia propuesta | Recuperación 1A | Estado de referencia |
|---|---|---|---|---|
| [F4-01](../artifacts/phase4_preparation/review_packets/F4-01.md) | Descarga binaria HttpClient sin evaluación | B01 | No vacía | complete_reference |
| [F4-02](../artifacts/phase4_preparation/review_packets/F4-02.md) | Bytes descargados y carga reflectiva funcional | B01+B02 | No vacía | partial_context_known_outer_operations |
| [F4-03](../artifacts/phase4_preparation/review_packets/F4-03.md) | Registro remoto de tarea de inicio de sesión | B03+B06 | No vacía | complete_reference |
| [F4-04](../artifacts/phase4_preparation/review_packets/F4-04.md) | Borrado de canal de laboratorio remoto inexistente | B04+B06 | No vacía | complete_reference |
| [F4-05](../artifacts/phase4_preparation/review_packets/F4-05.md) | Evento local convertido y enviado mediante PUT | B05+B06 | No vacía | complete_reference |
| [F4-06](../artifacts/phase4_preparation/review_packets/F4-06.md) | Credencial CLIXML leída y material de contraseña accedido | B07 | No vacía | complete_reference |
| [F4-07](../artifacts/phase4_preparation/review_packets/F4-07.md) | Compilación diferida almacenada sin invocación | [] | No vacía | complete_reference |
| [F4-08](../artifacts/phase4_preparation/review_packets/F4-08.md) | Generación IL local e invocación de suma inocua | B02 | No vacía | complete_reference |
| [F4-09](../artifacts/phase4_preparation/review_packets/F4-09.md) | Persistencia WMI con autenticación desde bóveda ficticia | B03+B06+B07 | Sin texto verificado relevante | complete_reference |
| [F4-10](../artifacts/phase4_preparation/review_packets/F4-10.md) | Deshabilitación de canal de laboratorio inexistente | B04 | Sin texto verificado relevante | complete_reference |
| [F4-11](../artifacts/phase4_preparation/review_packets/F4-11.md) | Consultas de tareas y firewall sin modificación | B05 | Sin texto verificado relevante | complete_reference |
| [F4-12](../artifacts/phase4_preparation/review_packets/F4-12.md) | Credencial interactiva ligada a autenticación remota | B06 | Sin texto verificado relevante | complete_reference |
| [F4-13](../artifacts/phase4_preparation/review_packets/F4-13.md) | Inspector de palabras de comando y comentario adversario | [] | Sin texto verificado relevante | complete_reference |
| [F4-14](../artifacts/phase4_preparation/review_packets/F4-14.md) | Compresión en memoria y codificación de bytes inocuos | [] | Sin texto verificado relevante | complete_reference |
| [F4-15](../artifacts/phase4_preparation/review_packets/F4-15.md) | Petición parametrizada con origen y método desconocidos | Indeterminado | Sin texto verificado relevante | indeterminate |
| [F4-16](../artifacts/phase4_preparation/review_packets/F4-16.md) | Inventario DNS local y callback de tabla desconocida | Indeterminado | Sin texto verificado relevante | partial_indeterminate_set |

## Cobertura propuesta

| Comportamiento | Unidades determinables positivas |
|---|---|
| B01 | F4-01, F4-02 |
| B02 | F4-02, F4-08 |
| B03 | F4-03, F4-09 |
| B04 | F4-04, F4-10 |
| B05 | F4-05, F4-11 |
| B06 | F4-03, F4-04, F4-05, F4-09, F4-12 |
| B07 | F4-06, F4-09 |

Dos unidades tienen conjunto completo indeterminado y se mantienen fuera de los denominadores de clasificación: F4-15 (sin etiquetas conocidas) y F4-16 (B05 conocida como mínimo, callback desconocido). Se evalúa la abstención/incertidumbre por separado.

Ocho textos tienen recuperación no vacía; ocho no. Los mecanismos de logging F4-04/F4-10 comparten bloque estadístico conservador `audit-control`: 16 textos, 15 bloques, 13 bloques entre los 14 determinables. Esta agrupación no convierte los restantes en una muestra aleatoria de una población.

La revisión de novedad debe consultar el [audit estructural y sus coincidencias más cercanas](../artifacts/phase4_preparation/proposal/independence_audit.json). Compartir una primitiva B01–B07 es inevitable; renombrarla no demuestra independencia.
