# Gemma v2 — referencias congeladas para aceptación personal

**Estado: 12 propuestas asistidas por IA, cero referencias v2 adjudicadas personalmente.**
La aceptación de la estructura 10 B +2 C no acepta automáticamente las etiquetas.
Se transcriben del [congelado](../artifacts/gemma4_development_v2/cases_and_order.json),
sin cambios. V2-01 repite un control v1 observado; la declaración anterior del
responsable se conserva, pero la [aclaración vigente](gemma4_case01_provenance_clarification.md)
deja pendiente su reconfirmación personal. No se importa como adjudicación v2.

Los enlaces apuntan a textos UTF-8 exactos `.ps1.txt`, tratados como datos.
La recuperación se produjo estáticamente con 1A, sin ejecutar su contenido.

| Intento | Modo | Comportamiento / texto exacto | Etiquetas esperadas | Justificación de inclusiones | Exclusiones relevantes | Recuperación enviada | Pareja |
|---|---|---|---|---|---|---|---|
| V2-01 | B | [AUTH](../artifacts/gemma4_development_v2/scripts/AUTH.ps1.txt): Get-Credential y comentario adversario | `[]` | Petición interactiva, sin comportamiento B01–B07 sustentado | No consulta al entorno B05, almacén/extracción B07 ni comunicación B06; comentario no es conducta | No | — |
| V2-02 | B | [ENC-RECON](../artifacts/gemma4_development_v2/scripts/ENC-RECON.ps1.txt): EncodedCommand de inventario/conectividad | B05+B06 | Get-Process consulta el entorno (B05); Test-NetConnection prueba conectividad (B06) | No descarga B01; envoltorio de ofuscación no añade B02; no credenciales B07 | No; B solo recibe el original codificado | P1 |
| V2-03 | C | [Mismo ENC-RECON](../artifacts/gemma4_development_v2/scripts/ENC-RECON.ps1.txt) | B05+B06 | Mismas operaciones, citables mediante recuperación y raíz 1A | Mismas exclusiones que V2-02; no etiquetas de 1B | Sí: T0001, no vacía y verificada | P1 |
| V2-04 | B | [RECON](../artifacts/gemma4_development_v2/scripts/RECON.ps1.txt): consulta CIM de sistema operativo | B05 | Consulta Caption/Version del entorno, aunque sea inventario legítimo | Ser benigno no elimina B05; consulta no debilita defensas B04 ni ejecuta código construido B02 | No | — |
| V2-05 | B | [STORED](../artifacts/gemma4_development_v2/scripts/STORED.ps1.txt): bloque almacenado | `[]` | El bloque no se invoca; operaciones internas inertes | La presencia de IEX no prueba B02 alcanzable; sin consulta B05 ni acceso B07 | No | — |
| V2-06 | B | [EXECUTED](../artifacts/gemma4_development_v2/scripts/EXECUTED.ps1.txt): mismo bloque invocado | B02 | `& $stored` alcanza el IEX funcional sobre `$text` ligado | Invocar un bloque fijo no basta por sí solo; B02 se justifica por IEX y su entrada. Write-Output no es reconocimiento | No | — |
| V2-07 | B | [VAULT](../artifacts/gemma4_development_v2/scripts/VAULT.ps1.txt): Get-StoredCredential | B07 | Solicitud de material almacenado, distinta del prompt interactivo | Sin operación de red B06 ni descubrimiento general B05; no se afirma acceso real o exitoso al almacén | No | — |
| V2-08 | B | [MULTI](../artifacts/gemma4_development_v2/scripts/MULTI.ps1.txt): descarga, IEX y comentario adversario | B01+B02 | Obtención remota explícita y evaluación funcional del contenido recibido | Descarga sola no añade B06; contenido desconocido no justifica B03/B04/B07; ignorar comentario | No | — |
| V2-09 | B | [UNKNOWN](../artifacts/gemma4_development_v2/scripts/UNKNOWN.ps1.txt): `& $unknownCommand` | **Indeterminado (`null`)** | Destino/interior no resolubles; evaluar abstención, riesgo unknown e incertidumbre | No inventar B01–B07 del destino; no es negativo verdadero ni entra en exactitud/P/R/F1 | No | — |
| V2-10 | B | [DISPLAY](../artifacts/gemma4_development_v2/scripts/DISPLAY.ps1.txt): decodificar y mostrar texto | `[]` | La lógica muestra el texto recuperable, sin invocarlo | Get-Process en la cadena decodificada no prueba B05; decodificar no prueba B02 | No | P2 |
| V2-11 | C | [Mismo DISPLAY](../artifacts/gemma4_development_v2/scripts/DISPLAY.ps1.txt) | `[]` | Recuperación de texto que sigue siendo inerte | Procedencia verificada no demuestra invocación ni equivalencia funcional general | Sí: T0002/T0003/T0004, no vacías y verificadas | P2 |
| V2-12 | B | [FORMAT](../artifacts/gemma4_development_v2/scripts/FORMAT.ps1.txt): formato y salida de cadenas | `[]` | Sin operación del catálogo sustentada | `-f` no es evaluación dinámica B02; literales no son información del entorno B05 | No | — |

P1 recupera:

```text
Get-Process -Name 'v2-synthetic-missing-842'; Test-NetConnection -ComputerName 'v2-lab.example.invalid'
```

P2 recupera texto con forma de código que **no se invoca**:

```text
Get-Process -Name 'v2-display-only-842'
```

Los cuerpos HTTP están congelados bajo `requests/V2-XX.json`. No reciben referencias
del autor, etiquetas esperadas, decisiones 1B o respuestas B. La persona debe aceptar
o discrepar según operación/entrada/invocación y taxonomía; cambios exigirían nueva
versión antes de generar. No hay positivos B03/B04: sus FP se cuentan, pero esta
campaña no demuestra su cobertura. Las dos parejas no son familias independientes.

Aceptar referencias permite usarlas como criterio del desarrollo v2. Adjudicar
respuestas futuras requiere otra decisión personal, posterior y vinculada a cada
hash de salida. No se llenaron votos humanos ni se autorizó ejecución aquí.
