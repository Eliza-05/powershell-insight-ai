# Procedencia de los bytes exportados de Git

Commit: `7fc29f86d50298207a2a480ac3989be175ec9cb1`.

Se verificaron los 180 archivos contra los dos archivos producidos por `git archive` y contra los blobs del commit. En esta instalación, `core.autocrlf=true`: 136 archivos exportados tienen representación CRLF distinta del blob. Se comprobó, archivo por archivo, que **todas esas diferencias se limitan a CRLF/LF**; los demás bytes coinciden. Los 44 restantes coinciden también byte por byte con el blob.

Los hashes del manifiesto describen los **bytes realmente exportados y ejecutados en AWS**, que se comprobaron después de transferir y al cerrar la validación. No deben confundirse con hashes SHA-256 del blob sin conversión. `git_export_representation.json` conserva, para cada conversión, ruta, ambos hashes y conteos de CRLF.

La primera comprobación adicional que exigía igualdad binaria directa con todos los blobs rechazó esta diferencia de representación; se investigó sin modificar fuentes y se dejó este registro explícito. No se transformó el código desplegado después de las pruebas ni después de la preparación F4. El hash normalizado de la política v2 siguió siendo `53d4cc36ca6b19dd5630065aabb0bd3d0a6f6627eb946989d32d6f773f10c081`; el hash de sus bytes desplegados está registrado en la estrategia nativa.

Para reproducir exactamente esta captura, usar sus archivos exportados y sus manifiestos de hashes. Una futura exportación con otra configuración de finales de línea deberá declarar sus propios hashes de bytes y verificar las diferencias antes de sellar. Este documento no cambia el candidato parcial ni concede aprobación científica.
