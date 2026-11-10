# Cierre técnico y experimental de PowerShell Insight AI

**Estado final:** CAMPAÑA DE FASE 4 COMPLETA Y EVALUADA. H1 y H2 no tienen apoyo; es un resultado negativo válido.
**Rama:** `integration/final-validation`, integrada en `develop` (SHA final en `CIERRE_GIT.md`).
**SHA científico (código ejecutado):** `41330339abc5ba8a73ca6b595c9ed4396d275e82`.
**Actualización:** 10 nov 2026, America/Bogota.
**Responsable:** Karol. **Ejecución técnica y redacción:** Claude (IA), a petición de Karol.

## Orden de lectura

1. [RESULTADOS_H1_H2.md](RESULTADOS_H1_H2.md): resultados, aprobaciones transcritas, incidentes y limitaciones.
2. [PROTOCOLO_FASE4.md](PROTOCOLO_FASE4.md): protocolo prospectivo aprobado, congelado en el candidato.
3. [INFORME_TECNICO.md](INFORME_TECNICO.md): arquitectura, cambios, infraestructura (AWS → GCP), pruebas e incidencias.
4. [CTX01_DIAGNOSTICO_Y_ENMIENDA.md](CTX01_DIAGNOSTICO_Y_ENMIENDA.md): causa y corrección del bloqueo de contexto.
5. [GUIA_DEMO.md](GUIA_DEMO.md): cómo encender, conectar y demostrar la aplicación.
6. [CIERRE_GIT.md](CIERRE_GIT.md): commits, merge y SHA final.
7. [EVIDENCIAS.md](EVIDENCIAS.md): inventario, hashes y ubicación del material restringido.
8. [PLAN_CIERRE_KAROL.md](PLAN_CIERRE_KAROL.md): plan original (9 nov), que se conserva como encargo.

## Estado de las puertas de cierre

| Elemento | Estado |
|---|---|
| CTX-01 (presupuesto de contexto) | **Resuelto**: enmienda aprobada (10 nov 09:47) y 32/32 solicitudes preparadas |
| Protocolo definitivo | **Aprobado** (10 nov 10:17) y congelado en el candidato |
| Revisión humana de las 16 referencias | **Hecha por Karol**: 16/16 aprobadas y ratificadas en el candidato final. No es independiente |
| FREEZE | **Sellado**: candidato `d960f81b`, FREEZE `f0468a2d` |
| Campaña F4 | **Completa**: 16 A + 32 intenciones LLM, 0 timeouts, 0 paradas. Hubo 2 intentos previos detenidos y conservados (1 intención gastada en total) |
| Revisión humana H2 | **Hecha por Karol**: 32/32 salidas, 200 afirmaciones |
| H1 | Δ micro-F1 (C−B) = 0,00; p = 1,0. **Sin apoyo** |
| H2 | Δ no respaldadas por unidad (C−B) = −0,03; p = 0,50. **Sin apoyo** |
| Validación funcional | Backend nativo 779/779 en GCP; frontend 141 + integración 11 + navegador (20/10/87); demo: ver `GUIA_DEMO.md` §8 |
| Merge final a `develop` | Ver `CIERRE_GIT.md` |

## Documentos de cierre

| Documento | Estado |
|---|---|
| [PLAN_CIERRE_KAROL.md](PLAN_CIERRE_KAROL.md) | Plan del 9 nov (encargo; no se reescribe) |
| [INFORME_TECNICO.md](INFORME_TECNICO.md) | Completo |
| [PROTOCOLO_FASE4.md](PROTOCOLO_FASE4.md) | Aprobado y congelado |
| [RESULTADOS_H1_H2.md](RESULTADOS_H1_H2.md) | Completo (H1 y H2) |
| [EVIDENCIAS.md](EVIDENCIAS.md) | Actualizado con la evidencia del cierre |
| [GUIA_DEMO.md](GUIA_DEMO.md) | Procedimiento y estado de reproducción |
| [CIERRE_GIT.md](CIERRE_GIT.md) | Commits, merge y SHA final |
| [CTX01_DIAGNOSTICO_Y_ENMIENDA.md](CTX01_DIAGNOSTICO_Y_ENMIENDA.md) | Enmienda aprobada |

## Antecedentes (9 nov)

La organización inicial de esta carpeta, del 9 nov, documentaba el estado "BLOQUEADO ANTES DEL FREEZE" en `7fc29f8` (AWS). Esa evidencia histórica se conserva sin cambios en `evidencias-publicables/aws`, `integracion`, `pruebas` y `evaluacion`. La evidencia nueva del cierre está en `evidencias-publicables/ctx01`, `validacion-final`, `herramientas` y en `evaluacion/EVALUACION_F4_CAMPANA3_AGREGADA.json`.

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
