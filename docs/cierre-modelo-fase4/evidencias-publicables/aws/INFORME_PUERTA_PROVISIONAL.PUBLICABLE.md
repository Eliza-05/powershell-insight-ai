> Copia publicable derivada de un informe historico. Rutas operativas redactadas y enlaces ajustados; no es una nueva validacion, acta humana o autorizacion. La responsabilidad vigente de Karol consta en el plan.

# Informe de autorización pendiente — PowerShell Insight AI

**Veredicto: BLOQUEADO ANTES DEL FREEZE.** El despliegue técnico funciona y el preflight pasó con observaciones. La preparación científica se detuvo por `proposal_context_budget_exceeded`; falta además la revisión humana confirmada como pendiente. Este paquete no es apto para sellar ni ejecutar.

## Comprobaciones requeridas

| Punto | Evidencia y resultado |
|---|---|
| 1. SHA y Git | `7fc29f86d50298207a2a480ac3989be175ec9cb1`, rama integration/final-validation, árbol limpio y remoto coincidente al desplegar. Exactamente cinco archivos del diff aprobado; sin operaciones Git de escritura |
| 2. Archivos | 171 archivos iniciales y nueve fuentes de preparación del mismo commit, verificados individualmente por SHA-256; secretos, .env, claves, entornos, modelos y resultados históricos excluidos |
| 3. Ubuntu | Python 3.13.18 independiente, dependencias fijadas, pip check correcto; **767 pruebas nativas aprobadas en 11,92 s**, con Ollama real bloqueado durante tests. Frontend 141 y build son evidencia local anterior, no pruebas nuevas de este SHA |
| 4. Almacenamiento | Ruta canónica registrada <ALMACEN_MODELO>; ancestro <ANCESTRO_VALIDADO>; dispositivo 202:1, montaje raíz /, ext4, capacidad 32.092.319.744 bytes |
| 5. CPU/RAM/disco | Ocho vCPU; RAM física 33,647,419,392 bytes; disponible limitada por cgroups 32,890,433,536; disco libre actual 8,369,348,608 bytes (7.795 GiB) |
| 6. Modelo | Ollama 0.40.15; qwen3-coder:30b, digest 06c1097efce0431c2045fe7b2e5108366e43bee1b4603a7aded8f21689e90bca; /api/ps vacío, sin generación |
| 7. Binding/evidencia | linux-model-filesystem-binding-v1; SHA real de STORAGE_METADATA_QUERIES_01.json = 192636e09e02add5e5b5291ef58530ffeff95e3fee9aa12afcc92a30aa8b16fa, igual al declarado. Captura canónica previa preservada; montaje/capacidad/espacio revalidados sin sudo |
| 8. Preflight | PREFLIGHT APROBADO CON OBSERVACIONES; política linux-resident-mode-aware-v1, overcommit 0, reserva fría completa 23,968,709,120 bytes; admisión true y motivos vacíos. No implica inferencia exitosa ni garantiza ausencia de OOM |
| 9. Propuesta Qwen3 | Nueva propuesta prospectiva y configuración documental; intento real de prepare conservado con **1 B, 0 C**. No llegó a crear configuración/orden/manifiesto completos del controlador |
| 10. Revisión humana | Confirmada pendiente por el responsable. Dieciséis fichas, 14 determinadas y dos indeterminadas; originales con hashes iguales a los anteriores; 0 aprobaciones. Plantillas sin nombres, firmas o decisiones ficticias |
| 11. Fallos | Propuesta en PROTOCOLO_QWEN3_PROVISIONAL.md: mantener 300 s, sin reintentos; raw/diagnóstico preservados; rechazo ordinario terminal separado de timeout/infraestructura/estado incierto crítico |
| 12. Métricas | H1 sobre aceptados del pipeline; null no es [] y positivos determinados faltantes cuentan como FN de cobertura. H2 sobre afirmaciones de crudos completos con revisión humana estricta; salidas no adjudicables no reciben cero favorable. Campaña parcial no habilita contraste completo |
| 13. Controlador | Mismo código publicado; CLI run exige autorización. Simulación independiente: 48 registros/32 intenciones ficticias, checkpoints, rechazo de duplicados, timeout e interrupción con intención huérfana bloqueados; sin FREEZE ni red real |
| 14. Autorizaciones/ledger | Protocolo definitivo, referencias, FREEZE, presupuesto y ejecución todavía no autorizados. Ningún ledger real ni directorio de ejecución científica creado; ledgers ficticios están solo bajo verification/controller_synthetic_02 |
| 15. Riesgos | Guarda de contexto bloqueante; revisión/independencia semántica pendientes; captura de ruta protegida no revalidada en vivo, concurrencia/OOM, ocho vCPU frente a diez hilos, timeout CPU de 300 s y limitaciones del verificador |
| 16. Presupuesto | Previsto 16 A + 16 B + 16 C; máximo 32 llamadas nuevas. **Autorizadas 0, intentadas 0, exitosas 0, fallidas 0; 32 propuestas sin consumir** |

## Incidente de preparación

Se ejecutó `python -B -m experiments.phase4 prepare` una sola vez, con perfil v2, binding operativo validado y conexiones al puerto real 11434 prohibidas. La guarda exige suma de bytes UTF-8 de los mensajes +512+2048 <=8192. La política ocupa 3241 bytes; el límite conjunto de mensajes es 5632. Esto describe la regla del código; no es un conteo de tokens real ni una prueba de capacidad del modelo.

El código rechazó la preparación antes de emitir la primera solicitud C. Se preservaron todos los archivos parciales y el traceback. No se reconstruyó el request rechazado para depurar, no se repitió prepare, no se ajustaron casos, política, estimador, parámetros, límites o código basándose en F4. Tampoco se ejecutaron A/B/C científicos. Las referencias authored se utilizaron después exclusivamente para el paquete humano solicitado.

No hay una corrección técnica autorizada que pueda declararse segura sin una decisión metodológica. El contrato vigente no permite completar esta propuesta. Antes de reconsiderarla, el responsable debe decidir si mantiene el bloqueo o abre un diseño prospectivo revisado; cualquier revisión debe registrar la exposición de estas entradas y valorar una nueva reserva independiente. No corresponde declarar esos mismos textos una evaluación virgen después de usarlos para ajustar una solución.

## Referencias y decisiones pendientes

El paquete incluye F4-01 a F4-16, hashes, referencias de IA, criterios de aceptación, plantilla de registro de revisores y de discrepancias. Una persona autorizada debe revisar activación, inclusiones/exclusiones, evidencia, novedad y agrupación, seguridad y los dos indeterminados. La revisión humana real no puede ser reemplazada por una respuesta genérica de aprobación ni por una ficha producida por IA.

La plantilla PROVISIONAL queda vinculada al hash de este paquete incompleto, para trazabilidad documental; no satisface Proposal.seal. Una vez exista candidato final técnicamente viable, habrá que confirmar su identidad y revisión. No se solicitan firmas de personas inexistentes ni se atribuyen aprobaciones al equipo.

Las hipótesis, taxonomía, métricas, error protocol, referencias originales y orden propuesto previo se documentan con procedencia. La propuesta Qwen14, sus resultados y documentos históricos se conservaron; no se usan como validación empírica de Qwen3. La independencia automática de esta preparación no llegó a ejecutarse por la parada anterior: no se declara aprobada.

## Reproducibilidad, recuperación y cierre

La nueva copia es `<COPIA_AISLADA>`. Conserva entorno propio y fuentes exactas del SHA. La propuesta parcial reside en artifacts/phase4_preparation; este paquete documental, en artifacts/phase4_review_PROVISIONAL. Los hashes del manifiesto incluyen código, evidencia, configuración documental, referencias y preparación parcial, con todos los estados de aprobación false.

Se comprobaron por sus hashes conocidos 1.645 archivos del repositorio histórico, 951 del laboratorio y 169 fuentes del despliegue anterior: **2.765 archivos sin cambios** dentro del alcance previo, que excluye privados/keys, .git, entornos, cachés y symlinks. No se alteró Ollama, permisos, modelo, puertos, kernel o servicios; no se usó sudo en esta continuación. No se realizaron commits, push, merges o cambios de rama.

No existe campaña científica activa, resultado F4 ni evaluación H1/H2. Todas sus métricas son no medidas, no cero. Se conservan originales remotos y se exporta el paquete junto con los logs/XML y hashes para copia local durable. No se detuvo la EC2; sus recursos siguen sujetos a concurrencia y la instancia permanece encendida.

Recomendación: **no autorizar el FREEZE de este candidato incompleto ni hacer merge científico a develop como si F4 estuviera cerrada**. La entrega académica puede respaldar el prototipo y las pruebas técnicas, declarando el bloqueo metodológico y la revisión pendiente. Resolverlos exige decisión del responsable, sin debilitar controles para obtener 32 inferencias.

**BLOQUEADO ANTES DEL FREEZE.**
