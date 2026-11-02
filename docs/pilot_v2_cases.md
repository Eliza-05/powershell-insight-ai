> **Estado vigente del lote:** aprobado globalmente por el responsable mediante la [instruccion de cierre](../experiments/reviews/pilot_v2_owner_global_approval.json). Esta ficha/formulario conserva el contenido de preparacion anterior a la congelacion. Sus casillas y estados pendientes son registros individuales historicos, no una nueva exigencia de 48 votos: no hubo revision humana individual independiente. El estado efectivo aprobado se registra por lote; ello no aprueba las salidas del modelo.

# Piloto v2 — 48 fichas para revision final

**Modelo unico decidido: qwen3.5:4b-q4_K_M. Las 48 fichas, los umbrales y la congelacion siguen pendientes; el modelo aun no esta validado.**

La correccion precongelacion de D03/D04 agrega la invocacion explicita del metodo compilado; conserva etiquetas, otras familias y prompt. Cada bloque contiene ocho fichas (cuatro familias).
Leer el codigo completo, la referencia decodificada cuando exista y todas las evidencias antes de decidir. Ningun texto se ejecuta.

Contrato de metricas y decisiones: [revision final](pilot_v2_final_review.md).

| Bloque | Casos | Familias | Estado |
|---|---|---|---|
| [development 1/3](pilot_v2_review_development_01.md) | V2-D01 a V2-D08 | 4 | pendiente |
| [development 2/3](pilot_v2_review_development_02.md) | V2-D09 a V2-D16 | 4 | pendiente |
| [development 3/3](pilot_v2_review_development_03.md) | V2-D17 a V2-D24 | 4 | pendiente |
| [selection 1/3](pilot_v2_review_selection_01.md) | V2-S01 a V2-S08 | 4 | pendiente |
| [selection 2/3](pilot_v2_review_selection_02.md) | V2-S09 a V2-S16 | 4 | pendiente |
| [selection 3/3](pilot_v2_review_selection_03.md) | V2-S17 a V2-S24 | 4 | pendiente |

Son 24 familias y 48 fichas; ninguna validacion humana de caso esta registrada. Solo se evaluara Qwen3.5 4B, con 102 llamadas o 126 si se usa la unica revision del prompt.

[Checklist por bloques](pilot_v2_review_checklist.md) · [Adjudicacion S04/S20 y criterios](pilot_v2_final_review.md)
