# Inventario y publicación controlada de evidencias

**Fecha:** 9 de noviembre de 2026, America/Bogota. **Rama:** `integration/final-validation`. **SHA de procedencia:** `7fc29f86d50298207a2a480ac3989be175ec9cb1`.

Esta entrega organiza evidencia existente para su futura conservación en Git. No incorpora nuevos resultados experimentales ni supone revisión humana o aprobación del FREEZE. Karol es la revisora designada de las 16 referencias y de las salidas que requiera H2; ambas revisiones siguen pendientes.

## Alcance y método

Se inventariaron todos los **4.080 archivos regulares** bajo `logs/`, recursivamente, sin seguir enlaces simbólicos ni expandir archivos comprimidos. El alcance encontrado fue:

| Directorio original | Archivos | Bytes |
|---|---:|---:|
| `logs/final_18f772e/` | 3.961 | 3.453.307 |
| `logs/final_7fc29f8/` | 119 | 4.913.949 |
| **Total** | **4.080** | **8.367.256** |

No aparecieron otros directorios de logs en esta inspección. El [inventario por archivo](evidencias-publicables/INVENTARIO_LOGS.json) contiene nombre/ruta relativa, tipo, tamaño, propósito, utilidad, sensibilidad, categoría, recomendación, SHA-256 y copia seleccionada cuando existe. Los códigos de propósito se definen dentro del propio JSON. Los archivos no seleccionados no se consideran aprobados para Git por figurar en el inventario.

Se calcularon hashes en flujo para preservar integridad; no se decodificaron ni interpretaron los payloads F4 protegidos. La revisión de contenido se limitó a las fuentes técnicas seleccionadas. El XML de pruebas se procesó para obtener agregados, sin publicar nombres/argumentos de casos ni salidas capturadas. No se encontraron nombres de credenciales/modelos que obligaran a omitir su lectura de hash dentro de este alcance; ello no certifica otros directorios del workspace. El `.env` privado y las claves SSH no se inspeccionaron.

## Clasificación A/B/C/D

| Categoría | Archivos originales | Tratamiento |
|---|---:|---|
| A — aptos para Git | 12 | Revisados; se preparó una copia idéntica de cada uno. El cambio de extensión de ciertos `.log` a `.txt` no cambia sus bytes |
| B — necesitan versión publicable o revisión | 107 | Se usaron 15 fuentes para crear 12 derivados revisados; los restantes permanecen sin aprobación de publicación |
| C — restringidos | 54 | Fuera de la selección publicable; inventario/hashes y acceso autorizado, sin contenido científico protegido |
| D — prescindibles para Git | 3.907 | Temporales de pruebas, cachés o archivos fuente intermedios; no se publican ni se eliminan automáticamente |

El [manifiesto de publicación](evidencias-publicables/MANIFIESTO_PUBLICACION.json) contiene **24 copias de 27 fuentes**, sus hashes y transformaciones. El inventario y el manifiesto son dos artefactos documentales adicionales, no copias de resultados científicos.

## Originales y copias preparadas

Cada fila distingue el original preservado y el archivo publicable. En A, ambos hashes son iguales. En B, los hashes diferentes corresponden a una derivación declarada: omisión de rutas personales/operativas, resúmenes por campos permitidos, cambio de codificación, retirada de detalles de pruebas o ajuste de enlaces. No se alteran datos originales para hacer coincidir checksums.

| Copia preparada | Original(es) y SHA-256 | SHA-256 publicable |
|---|---|---|
| [LOCAL_RECOVERY_VERIFIED.json (A)](evidencias-publicables/aws/LOCAL_RECOVERY_VERIFIED.json) | `logs/final_7fc29f8/LOCAL_RECOVERY_VERIFIED.json`<br>`21ba5641d503cd17b6c999a89383f6c25fa35671d55a0678ad1977472121a653` | `21ba5641d503cd17b6c999a89383f6c25fa35671d55a0678ad1977472121a653` |
| [final_export_receipt.json (A)](evidencias-publicables/aws/final_export_receipt.json) | `logs/final_7fc29f8/final_export_receipt.json`<br>`e5a183a4529062ca207e98151cf6ae4e6feedb47ae5cff720ae8eac4f1cd2dcb` | `e5a183a4529062ca207e98151cf6ae4e6feedb47ae5cff720ae8eac4f1cd2dcb` |
| [deployment_verified.json (A)](evidencias-publicables/aws/deployment_verified.json) | `logs/final_7fc29f8/deployment_verified.json`<br>`b6976796e677380e4db0d21112b5907326cd68831d9fda2ab5322060fc644c3d` | `b6976796e677380e4db0d21112b5907326cd68831d9fda2ab5322060fc644c3d` |
| [git_audit.json (A)](evidencias-publicables/integracion/git_audit.json) | `logs/final_7fc29f8/git_audit.json`<br>`74a160443660c6aee579ff52f90b1a5197324ec41aa7e089593ed427f1d87855` | `74a160443660c6aee579ff52f90b1a5197324ec41aa7e089593ed427f1d87855` |
| [git_export_representation.json (A)](evidencias-publicables/integracion/git_export_representation.json) | `logs/final_7fc29f8/git_export_representation.json`<br>`5634207318233d48527249edf355808cd3f2550e276a731b4d7047b729fb7b42` | `5634207318233d48527249edf355808cd3f2550e276a731b4d7047b729fb7b42` |
| [PROCEDENCIA_EXPORTACION_GIT.md (A)](evidencias-publicables/integracion/PROCEDENCIA_EXPORTACION_GIT.md) | `logs/final_7fc29f8/PROCEDENCIA_EXPORTACION_GIT.md`<br>`a038633b4f15c67056e7b149be0682719ae6bcb8e07816435a5eb77e60f6823b` | `a038633b4f15c67056e7b149be0682719ae6bcb8e07816435a5eb77e60f6823b` |
| [aws_validation_summary.json (A)](evidencias-publicables/pruebas/aws_validation_summary.json) | `logs/final_7fc29f8/aws_validation_summary.json`<br>`81f795493f1f170736af4be5aa861c49b81de61eb230dbc140683962986c335d` | `81f795493f1f170736af4be5aa861c49b81de61eb230dbc140683962986c335d` |
| [aws_controller_synthetic_audit.json (A)](evidencias-publicables/pruebas/aws_controller_synthetic_audit.json) | `logs/final_7fc29f8/aws_controller_synthetic_audit.json`<br>`d03268aa507d431d515c215c45383539030057357274efc7da81fd77bc9de6f0` | `d03268aa507d431d515c215c45383539030057357274efc7da81fd77bc9de6f0` |
| [aws_pip_freeze.txt (A)](evidencias-publicables/pruebas/aws_pip_freeze.txt) | `logs/final_7fc29f8/aws_pip_freeze.log`<br>`6c48ce3726d64b137b7c6056b730f7baacff8bb8292aea9d990272937c24c333` | `6c48ce3726d64b137b7c6056b730f7baacff8bb8292aea9d990272937c24c333` |
| [aws_pip_check.txt (A)](evidencias-publicables/pruebas/aws_pip_check.txt) | `logs/final_7fc29f8/aws_pip_check.log`<br>`9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09` | `9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09` |
| [aws_cli_help.txt (A)](evidencias-publicables/integracion/aws_cli_help.txt) | `logs/final_7fc29f8/aws_cli_help.log`<br>`5b647217d65f158839a2588d9f55995825b900d1e892e17f42e91e88b72697c0` | `5b647217d65f158839a2588d9f55995825b900d1e892e17f42e91e88b72697c0` |
| [aws_cli_run_help.txt (A)](evidencias-publicables/integracion/aws_cli_run_help.txt) | `logs/final_7fc29f8/aws_cli_run_help.log`<br>`cd3050ee744dd55819679a357324a8bfcdd48f83703ea3d81ee9e995d896defa` | `cd3050ee744dd55819679a357324a8bfcdd48f83703ea3d81ee9e995d896defa` |
| [INFORME_FINAL_ESTADO.PUBLICABLE.md (B)](evidencias-publicables/aws/INFORME_FINAL_ESTADO.PUBLICABLE.md) | `logs/final_7fc29f8/INFORME_FINAL_ESTADO.md`<br>`79845c74a0a837b10dd53b8f4db23068354be0770e0da63c5e6df1839fa95468` | `3b1208e667c2453dc80f9f569698eebabe575b49be8ba11e6ef10aa6b97d6cda` |
| [INFORME_PUERTA_PROVISIONAL.PUBLICABLE.md (B)](evidencias-publicables/aws/INFORME_PUERTA_PROVISIONAL.PUBLICABLE.md) | `logs/final_7fc29f8/recovered/phase4_review_PROVISIONAL/INFORME_PUERTA_PROVISIONAL.md`<br>`ae3e85f7321449345e41ffe8be33994d6d832ad128451f02d9ea1c6a2c12c178` | `8d68dcd787e870925073ea915b65381b887880f31e4f3d7f24b195d6cc44bc86` |
| [INFORME_VALIDACION_PROVISIONAL.18f772e.PUBLICABLE.md (B)](evidencias-publicables/aws/INFORME_VALIDACION_PROVISIONAL.18f772e.PUBLICABLE.md) | `logs/final_18f772e/INFORME_VALIDACION_PROVISIONAL.md`<br>`1fdd76e800daad4771072b5ab5845c79643533e4c0564dd8c811fc15fdd9f881` | `c206326f085cf36326cf658374f930220e0cafe814455c68f2a91a6d32fcdd47` |
| [PROTOCOLO_QWEN3_PROVISIONAL.PUBLICABLE.md (B)](evidencias-publicables/evaluacion/PROTOCOLO_QWEN3_PROVISIONAL.PUBLICABLE.md) | `logs/final_7fc29f8/PROTOCOLO_QWEN3_PROVISIONAL.md`<br>`ad9c1b9767bb22fd4c343567e26f3cda03869f1296277c5aa4d3580363eecbad` | `d18a3e65d54943a802edc9f5f5ce2dfd08e33673d9c84ed4c4958c465b806a5e` |
| [aws_native_tests.PUBLICABLE.txt (B)](evidencias-publicables/pruebas/aws_native_tests.PUBLICABLE.txt) | `logs/final_7fc29f8/aws_native_tests.log`<br>`9bbcc25f658e898c9a6089f8d16fb29b7b42dfdc865275cbd7b685ef1cf28420` | `57e532d4fc62310932e015ff07e7173514360a576b171fd34a50944c19816ee2` |
| [local_frontend.PUBLICABLE.txt (B)](evidencias-publicables/integracion/local_frontend.PUBLICABLE.txt) | `logs/final_18f772e/local_frontend.log`<br>`6109e2e69239f2aabd2c968bac87ab56b0377fa69f14c7550fe88b47ad7fd256` | `2d1207efdcb5a944a3dfc22767b0c69f7461d95e5da869cdd26997414918af4b` |
| [local_frontend_build.PUBLICABLE.txt (B)](evidencias-publicables/integracion/local_frontend_build.PUBLICABLE.txt) | `logs/final_18f772e/local_frontend_build.log`<br>`39058044e136d5595895ec40836b7572327426274a1980043d770cfc0a30f499` | `662a0e04d7a694e6d8577e661d885ba73f49d6da8f71da9c1213485c78174fc4` |
| [RESUMEN_PYTEST.PUBLICABLE.json (B)](evidencias-publicables/pruebas/RESUMEN_PYTEST.PUBLICABLE.json) | `logs/final_7fc29f8/aws_native_tests.xml`<br>`a7ee1151c2f769c8faba7d59ef59016919e3b118ca104c58146876e36fe76d18` | `9c91f2b86235a5f8c378ef626d6d71c696a07b6d8204e82d20b335dad50d59bd` |
| [RESUMEN_PREFLIGHT.PUBLICABLE.json (B)](evidencias-publicables/aws/RESUMEN_PREFLIGHT.PUBLICABLE.json) | `logs/final_7fc29f8/recovered/validation_evidence/final_runtime_state.json`<br>`30544309ad46041128e6e8f1d106ed1ec566ffbe9cba7e573b1b0fedcdd1fa6a` | `b82fbcea2e861e37f8bb1a8a7206bf0f990e49b5ba7ffda10db4ef5c7bd8b51b` |
| [RESUMEN_ALMACENAMIENTO.PUBLICABLE.json (B)](evidencias-publicables/aws/RESUMEN_ALMACENAMIENTO.PUBLICABLE.json) | `logs/final_7fc29f8/model_storage_binding.PROVISIONAL.json`<br>`c5a09087c8a2ad8b74ed0e8448b670b6f68c491f0849b3e8b8c5d97a53f7eb3b`<br>`logs/final_7fc29f8/STORAGE_METADATA_QUERIES_01.json`<br>`192636e09e02add5e5b5291ef58530ffeff95e3fee9aa12afcc92a30aa8b16fa` | `b6e04bf4f0c115c67739f07b2c1b93f6079283755073f4f7f36271e33d6bcc67` |
| [SITUACION_EXPERIMENTAL.PUBLICABLE.json (B)](evidencias-publicables/evaluacion/SITUACION_EXPERIMENTAL.PUBLICABLE.json) | `logs/final_7fc29f8/aws_partial_preparation_inventory.json`<br>`15a73a467d328cb34cb0e3f5b1a8712a5a451e87f752088137bb85911cd725d9`<br>`logs/final_7fc29f8/aws_prospective_preparation_receipt.json`<br>`1999a8a2cfb014f67d80d5b808280ab239a6668334c1f9db5cfe8d3f41d9588e`<br>`logs/final_7fc29f8/aws_prospective_preparation.log`<br>`8dbecea8936fbc71084f1ffdadc5073e141182dc0101423576257a1a9c5249bd` | `76999f69b611d73948737f94555ec01503e5fe84058717277d969890037ab536` |
| [PRESERVACION_HISTORICOS.PUBLICABLE.json (B)](evidencias-publicables/aws/PRESERVACION_HISTORICOS.PUBLICABLE.json) | `logs/final_7fc29f8/recovered/validation_evidence/preservation_receipt.json`<br>`b999adfe8a9cc68679fa7468f371820b2f5fae9c267aca3ccbbd660959821c7e` | `af941cff363e253607c2130fdca9fc02b1d315440b02a74305edbca251d7d94f` |

## Qué se depuró y qué conserva su alcance histórico

- Se retiraron rutas personales absolutas, nombres de directorios de servidor, dispositivo/montaje identificable, plantillas completas del modelo y detalles de procesos que no eran necesarios para el resumen.
- Los informes Markdown derivados incluyen una advertencia de captura histórica; no son validaciones nuevas ni reemplazan el plan vigente. No se reasignan aprobaciones o revisiones mediante una copia documental.
- Los resúmenes de preflight y almacenamiento conservan métricas y comprobación de la evidencia real, pero son **no ejecutables**: no deben pasarse al controlador como bindings o configuración.
- Los tests se distinguen de inferencias. La auditoría de 48 registros/32 intenciones es una simulación; sus pruebas de timeout/interrupción no consumieron presupuesto F4.
- El resumen de preparación registra el fallo y los contadores 1 B/0 C, sin requests, originales o referencias. H1/H2 siguen sin evaluar.
- Los informes de `18f772e` documentan un estado anterior al despliegue `7fc29f8`; no representan el estado actual de AWS. Algunas fuentes originales usan UTF-16 y las versiones depuradas son UTF-8, con hashes nuevos.
- Se preserva la diferencia de representación Git LF/CRLF. El informe y la matriz de ambos hashes permiten distinguir blob y archivo exportado; no se reescribieron fuentes, políticas o evidencias congeladas.

<a id="material-restringido"></a>
## Material restringido y ubicación de originales

Las siguientes rutas son **referencias relativas al workspace original**, no enlaces a archivos que deban estar en un clon público. Sus hashes proceden del inventario; no se abrieron los contenedores para volver a inspeccionar los casos.

| Original restringido | Tipo/proposito | SHA-256 |
|---|---|---|
| `logs/final_7fc29f8/review_package_PROVISIONAL.tar.gz` | Paquete con referencias y fichas F4 | `076f25757eb452af2eac5779bff2dcc447598715354da88f5daaca496b669782` |
| `logs/final_7fc29f8/partial_preparation_preserved.tar.gz` | Intento parcial preservado con entradas/request | `bb0c2f8ac08e18f04fc7143a5223c5c0e982ecc7737acc8cafe3644c941d251e` |
| `logs/final_7fc29f8/validation_evidence.tar.gz` | Contenedor operativo completo sin depuracion para Git | `69944dce90e96ea741fccccb2534543eb7aafc3082a51bc829f9d88df71b23f6` |
| `logs/final_7fc29f8/scientific-sources.tar` | Fuente de preparacion que contiene material reservado | `c445751f626bed18b8b2c4043309f0fe284362541e818542a3d7f48d795ced19` |
| `logs/final_7fc29f8/prior_development_inputs.json` | Corpus original de entradas de desarrollo; no seleccionado para divulgacion | `9dd273620b62b9fabbc972aa2ff516cb03502b0c4f481a2bd502a4bea44f1cf8` |

Además deben permanecer fuera de Git:

- Las fichas individuales bajo `logs/final_7fc29f8/recovered/phase4_review_PROVISIONAL/review_packets/`, sus referencias y originales, y la preparación parcial bajo `logs/final_7fc29f8/recovered/phase4_preparation_partial/`.
- Cualquier acta, ledger, autorización o respuesta que contenga material sensible. No existe un ledger científico real nuevo ni autorizaciones de inferencia aprobadas en la evidencia actual; no se debe confundir la auditoría simulada con esos archivos futuros.
- Credenciales, claves, `.env`, pesos o información privada de AWS, incluso si aparecieran en un inventario posterior. Su inclusión en logs no los convierte en publicables.

**Acceso y custodia:** Karol deberá confirmar la disponibilidad, permisos y destinatarios autorizados de esos originales, y registrar el almacenamiento/backup real que se adopte. Esta tarea no creó un servicio de acceso controlado ni certificó ACL. `logs/` ignorado por Git es la ubicación local observada, no una política de seguridad. No se inventa un enlace a una nube o un repositorio privado inexistente. Para otra máquina se necesita un traspaso autorizado con verificación de hashes.

<a id="originales-no-publicados"></a>
## Originales técnicos no publicados todavía

Otros JSON con inventarios operativos completos, scripts auxiliares de despliegue/auditoría, traces o informes no seleccionados permanecen en B o D, según el inventario. Entre ellos están el arnés `native_storage_probe.py` y el seguimiento original de almacenamiento. No son un CLI público ni quedan aprobados para ejecutarse o publicarse automáticamente. Localizarlos por la ruta/ID del inventario y solicitar acceso al custodio cuando sean necesarios; revisar sus entradas, permisos, hashes y salidas antes de usarlos.

No se publicó todo `logs/`, no se cambió `.gitignore` y no se eliminó ningún temporal. Las copias de registros `.log` usan extensión `.txt` para respetar las reglas existentes, documentando ese cambio de nombre. Los documentos definitivos futuros continúan pendientes según el [README](README.md).

## Integridad y comprobaciones de publicación

- Antes y después de la preparación, los 4.080 originales conservaron tamaño, fecha de modificación y hash SHA-256. No se escribieron originales de logs.
- Las 12 copias A son idénticas byte a byte a sus fuentes. Los 12 derivados B tienen origen, transformaciones y hash de salida identificados.
- Los hashes del manifiesto pueden comprobarse desde la raíz con `Get-FileHash -Algorithm SHA256 -LiteralPath 'RUTA_REAL'` o `sha256sum`, usando el hash esperado correspondiente al original o a la copia, sin confundirlos.
- El inventario está vinculado mediante `inventory_sha256` en el manifiesto. Para evitar autorreferencia, el manifiesto no incluye su propio hash; un recibo externo puede registrar el hash del manifiesto si se requiere.
- Los enlaces públicos deben resolver sin depender de logs ignorados. Las ubicaciones restringidas se expresan como rutas textuales e IDs/hashes, sin publicar sus contenidos.
- Se revisa la selección en busca de rutas personales, claves/tokens, direcciones de infraestructura y estructuras de inputs/referencias. La inspección es un control documental del alcance seleccionado, no una certificación de todos los archivos privados del proyecto.

**Estado Git:** archivos preparados para revisión posterior, sin `git add`, commit, push o merge. La rama base y el cierre final de `develop` asignado a Karol se mantienen. Ninguna evidencia preparada aquí aprueba referencias, FREEZE, inferencias o enmiendas científicas.

<a id="cierre-10-nov"></a>
## Evidencia del cierre (10 nov 2026)

### Publicable en Git

| Archivo | Contenido |
|---|---|
| `evidencias-publicables/ctx01/CALIBRACION_TOKENS_DESARROLLO.json` (sha256 `f846d7e7…`) | 207 llamadas de desarrollo y selección (nunca F4): tokens por byte |
| `evidencias-publicables/validacion-final/ENTORNO_GCP_Y_CANDIDATO.json` | Entorno GCP, binding, pruebas nativas y preparación del primer candidato |
| `evidencias-publicables/validacion-final/VALIDACION_FRONTEND_SINTETICA.json` | Frontend, integración HTTP y navegador (sintético) |
| `evidencias-publicables/evaluacion/EVALUACION_F4_CAMPANA3_AGREGADA.json` | Agregados oficiales de H1/H2 y contadores, sin contenido F4 |
| `evidencias-publicables/herramientas/*.py` | Generadores de los formularios de revisión personal y el divisor de H2 |

### Restringido (fuera de Git)

| Ubicación | Contenido | SHA-256 |
|---|---|---|
| VM GCP `psi-cierre`: `~/psi-sci-4133033-r3/artifacts/phase4_preparation/` | Candidato final, FREEZE, ejecución (ledger, 48 resultados, checkpoints) y evaluaciones | Manifiesto `d960f81b…`, FREEZE `f0468a2d…`, evaluación final `15ff07f7…` |
| VM: `~/psi-sci-4133033/` y `~/psi-sci-4133033-r2/` | Campañas 1 y 2, detenidas, con STOP conservado | Ver `~/psi-evidence/run-r2_final_hashes.txt` |
| VM: `~/psi-evidence/` | Binding (`65d5dc7c…`) y su evidencia (`61e6111e…`), revisiones de Karol (`c5246441…`, `73c398dc…`, `e0f6190d…`), revisión H2 (`9ad26920…`) y su división (`2a6dcb0c…`), autorizaciones (`846be19f…`, `659fbd18…` rechazada por hora truncada, `a3e56508…`, `7ccbb881…`), logs, pruebas de velocidad | Ver cada archivo |
| PC de Karol: `Descargas\psi-evidencia-RESTRINGIDA\psi-evidence-backup-20261110T173926Z.tgz` | Respaldo de las campañas 1 y 2 y de `psi-evidence` en ese momento | `d5c60127…` |
| PC de Karol: `Descargas\psi-evidencia-RESTRINGIDA\psi-evidence-r3-20261110T184609Z.tgz` | Respaldo de la campaña 3 (ejecución, FREEZE, manifiesto, configuración, orden) y de `psi-evidence` | `9c4be707…` |
| PC de Karol: `Descargas\psi-evidencia-RESTRINGIDA\psi-evidence-final-20261110T191331Z.tgz` | **Respaldo final:** las 3 campañas, el candidato final completo, las evaluaciones, la revisión H2 y su división, la demo y `psi-evidence` | `744cb6cd…` |
| PC de Karol: `Descargas\psi-revision-F4\` y `Descargas\revision_referencias_F4_Karol*.json` | Formularios con contenido F4 y descargas de las revisiones | — |

**Custodia:** Karol. Estas ubicaciones son la custodia real observada al cerrar. **La VM de GCP es un almacenamiento temporal:** antes de borrarla, conviene copiar `~/psi-sci-4133033*/artifacts/phase4_preparation/` y `~/psi-evidence/` completos a un almacenamiento duradero autorizado por el equipo. Los respaldos de arriba cubren la ejecución, pero no todos los temporales.
