# Cierre técnico y experimental de PowerShell Insight AI

**Estado documentado:** BLOQUEADO ANTES DEL FREEZE. **Rama de trabajo:** `integration/final-validation`. **SHA de las últimas validaciones conservadas:** `7fc29f86d50298207a2a480ac3989be175ec9cb1`. **Actualización documental:** 9 de noviembre de 2026, America/Bogota.

Esta carpeta reúne el plan de Karol y evidencia técnica preparada para conservarse posteriormente en Git. Esta organización no ejecuta actividades experimentales, no aprueba referencias y no constituye un FREEZE. Las copias son históricas; no se hizo una nueva consulta a AWS ni una nueva ejecución de pruebas para producirlas.

## Responsabilidades y orden de lectura

Karol completa el cierre técnico, científico, operativo, documental y la integración final a `develop`. Realizará personalmente la revisión de las **16 referencias** y, después de las inferencias autorizadas, la revisión semántica necesaria para **H2**. Ambas tareas están pendientes. Si participó en construir referencias o preparar la evaluación, declarará esa participación y no calificará su revisión como independiente. Un requisito metodológico vigente que no se satisfaga necesita enmienda prospectiva o decisión formal aprobada; no se simulará mediante cambios de validadores.

1. Leer el [plan de cierre](PLAN_CIERRE_KAROL.md): conserva las 24 secciones, prioridades, dependencias, pruebas, permisos y merge final a `develop`.
2. Consultar [EVIDENCIAS.md](EVIDENCIAS.md): alcance, categorías A/B/C/D, originales, copias y hashes.
3. Revisar el [estado técnico publicable](evidencias-publicables/aws/INFORME_FINAL_ESTADO.PUBLICABLE.md) y el [resumen experimental](evidencias-publicables/evaluacion/SITUACION_EXPERIMENTAL.PUBLICABLE.json).
4. Resolver el bloqueo de contexto y las decisiones prospectivas; realizar y documentar Karol su revisión humana antes de solicitar el FREEZE.

## Estado de las puertas de cierre

| Elemento | Estado y alcance |
|---|---|
| Validación técnica conservada | 767 pruebas nativas aprobadas y preflight aprobado con observaciones en el SHA indicado; no acredita inferencia exitosa |
| Bloqueo de preparación | `proposal_context_budget_exceeded`; intento conservado con 1 request B y 0 C, sin repetirlo ni adaptar F4 |
| Revisión humana de referencias | Pendiente; revisora designada: Karol; 14 casos determinados y dos indeterminados |
| Protocolo científico definitivo | Pendiente; el borrador publicable es una propuesta histórica incompleta |
| FREEZE definitivo | Pendiente / no creado en la evidencia conservada |
| Campaña F4 | Pendiente / no ejecutada; 0 inferencias reales registradas, 32 previstas sin autorizar |
| Revisión humana de salidas H2 | Pendiente; responsable: Karol, después de la campaña autorizada |
| Resultados H1/H2 | No evaluados; no existen métricas reales que completar en informes futuros |
| Merge final a `develop` | Pendiente, asignado a Karol tras cerrar el alcance técnico, experimental, funcional y documental y obtener las revisiones correspondientes |

## Documentos de cierre

| Documento | Estado |
|---|---|
| [PLAN_CIERRE_KAROL.md](PLAN_CIERRE_KAROL.md) | Actualizado: revisión directa de Karol, evidencias, cierre técnico y merge final |
| [EVIDENCIAS.md](EVIDENCIAS.md) | Creado: inventario y correspondencia entre originales/copias publicables |
| `INFORME_TECNICO.md` | Pendiente: informe definitivo, sin sustituir las capturas históricas |
| `PROTOCOLO_FASE4.md` | Pendiente: protocolo definitivo y aprobaciones prospectivas |
| `RESULTADOS_H1_H2.md` | Pendiente: resultados reales o impedimento formal, sin cifras ficticias |
| `GUIA_DEMO.md` | Pendiente: procedimiento comprobado con fixtures sintéticos y permisos |
| `CIERRE_GIT.md` | Pendiente: commits, revisión, merge, pruebas y SHA final publicado de `develop` |

Los nombres pendientes no son enlaces a archivos inexistentes. Las copias de informes bajo `evidencias-publicables/` no sustituyen esos entregables definitivos.

## Evidencias preparadas para Git

```text
docs/cierre-modelo-fase4/
├── README.md
├── PLAN_CIERRE_KAROL.md
├── EVIDENCIAS.md
└── evidencias-publicables/
    ├── INVENTARIO_LOGS.json
    ├── MANIFIESTO_PUBLICACION.json
    ├── integracion/
    ├── aws/
    ├── pruebas/
    └── evaluacion/
```

Las cuatro subcarpetas contienen evidencia real seleccionada: integración/build y procedencia Git; despliegue/preflight/almacenamiento; pruebas/validación y controlador simulado; y estado/protocolo científico provisional. La carpeta `evaluacion/` no contiene respuestas F4 ni una evaluación H1/H2 ejecutada.

El [inventario completo](evidencias-publicables/INVENTARIO_LOGS.json) cubre **4.080 archivos** regulares de `logs/final_18f772e/` y `logs/final_7fc29f8/`. No se encontraron otros directorios bajo `logs/` en la inspección. La clasificación es: **A: 12**, **B: 107**, **C: 54**, **D: 3.907**. Se prepararon **24 copias** de **27 fuentes**: 12 copias A idénticas y 12 derivados B revisados. No se copió automáticamente todo lo clasificado como B.

- **A — aptos:** evidencia revisada que puede conservarse sin cambiar sus bytes; algunos `.log` se renombran a `.txt` sin alterar el contenido.
- **B — requieren versión publicable:** informes con rutas o detalles operativos, o material pendiente de revisión. Solo los derivados seleccionados y depurados están en esta carpeta.
- **C — restringidos:** originales F4, referencias, solicitudes, paquetes científicos/operativos y otros materiales que no deben incorporarse como contenido público.
- **D — prescindibles para Git:** temporales, cachés e intermedios duplicados; se conservaron sus originales sin borrarlos.

El [manifiesto de publicación](evidencias-publicables/MANIFIESTO_PUBLICACION.json) identifica fuentes, destinos, transformaciones y SHA-256. `logs/` y las reglas de `.gitignore` permanecen intactos. Los archivos están **preparados, sin `git add`, commit, push o merge**.

## Acceso a material restringido

El [índice de material restringido](EVIDENCIAS.md#material-restringido) conserva ubicaciones relativas y hashes de paquetes, sin enlazar a fichas o solicitudes inexistentes en un clon público. No debe interpretarse que ignorar una carpeta en Git configura permisos de acceso. Karol deberá verificar el canal, almacenamiento y autorizaciones reales antes de compartir los originales.

Las evidencias publicables pueden inspeccionarse desde un clon sin `logs/`. Para reproducir operaciones o revisar F4 se necesitan los originales y aprobaciones correspondientes; un resumen depurado no es un binding ejecutable ni un acta humana.
