"""Offline human-review presentation; no case changes and no semantic approval."""

from __future__ import annotations

import json
from collections import Counter

SOURCE_FENCE = "```powershell"

SPECIAL_READINGS = {
    "V2-DEV-F02": "B02 se propone por la cadena fuente C# -> Add-Type -> [AcademicBanner]::Text(). La invocacion explicita usa el tipo compilado y retornaria lab only si la compilacion/carga tiene exito; no se ejecuto. D04 codifica exactamente el cuerpo de D03 en UTF-16LE/Base64. Correccion anterior a congelacion; confirmacion humana pendiente.",
    "V2-DEV-F03": "B03 exige las tres piezas: action con ejecutable fijo, trigger AtLogOn y registro que enlaza ambos. El path inexistente no prueba exito ni elimina el intento de configurar inicio futuro.",
    "V2-DEV-F04": "Get-MpPreference consulta (B05); Add-MpPreference con ExclusionPath cambia configuracion defensiva (B04). La consulta no es evidencia de modificacion.",
    "V2-DEV-F07": "Retrieve usa la URL como clave de un almacen local; RetrievePassword intenta poblar material de credencial almacenada (B07), no establece comunicacion de red. Disponibilidad WinRT y existencia del registro no verificadas.",
    "V2-SEL-F03": "B03 depende del enlace APPDATA -> carpeta Startup -> archivo .cmd escrito por Set-Content. Se configura contenido para inicio de sesion; no se afirma que se escribiera ni que se ejecutara.",
    "V2-SEL-F04": "La lectura RunOnce es B05 y no B03. Enabled=$false cambia un perfil de firewall (B04). Test-NetConnection tiene destino/puerto propios (B06) y no demuestra descarga.",
    "V2-SEL-F07": "B07 se propone por lectura de exportacion declarada de terceros, ruta del escenario y seleccion de user/password conjuntamente. No basta el nombre password. La interpretacion depende del rol sintetico declarado del recurso: el responsable debe aceptarlo; no se ha probado que exista contenido real de credenciales.",
    "V2-SEL-F11": "Solo se conoce el despacho por & hacia un valor no resoluble. No se asigna B02 automaticamente, ni se conoce ausencia real de otras operaciones. Exact match de etiquetas=N/A; se revisan abstencion e incertidumbre por separado.",
    "V2-SEL-F12": "El texto permite fijar B01+B02 exteriores por respuesta HTTP -> Content -> Create -> Invoke. Los efectos del cuerpo remoto ausente siguen desconocidos; esta incertidumbre no hace indeterminadas las dos etiquetas exteriores.",
}


def build_review_materials(manifest: dict, annotations: list[dict], source_assets: dict[str, bytes]) -> dict[str, bytes]:
    result = {}
    cases = manifest["cases"]
    by_ann = {a["case_id"]: a for a in annotations}
    by_family = {f["family_id"]: f for f in manifest["families"]}
    case_audits = []
    index = ["# Piloto v2 — 48 fichas para revision final", "",
             "**Modelo unico decidido: qwen3.5:4b-q4_K_M. Las 48 fichas, los umbrales y la congelacion siguen pendientes; el modelo aun no esta validado.**", "",
             "La correccion precongelacion de D03/D04 agrega la invocacion explicita del metodo compilado; conserva etiquetas, otras familias y prompt. Cada bloque contiene ocho fichas (cuatro familias).",
             "Leer el codigo completo, la referencia decodificada cuando exista y todas las evidencias antes de decidir. Ningun texto se ejecuta.", "",
             "Contrato de metricas y decisiones: [revision final](pilot_v2_final_review.md).", "",
             "| Bloque | Casos | Familias | Estado |", "|---|---|---|---|"]
    checklist = ["# Piloto v2 — checklist por bloques de revision", "",
                 "**48 decisiones de caso pendientes.** La decision de usar solo Qwen3.5 4B no valida etiquetas, evidencias, umbrales ni calidad del modelo.", "",
                 "No registrar nombre, firma, fecha de revision ni aprobacion de un caso sin confirmacion expresa real.",
                 "El registro de decisiones individuales sigue en `experiments/reviews/pilot_v2_human_review.json`; no se rellena automaticamente.", "",
                 "Para cada ficha: verificar etiquetas y exclusiones; fragmentos y relaciones; riesgo y supuestos; incertidumbre/inyeccion; familia y variante.",
                 "En S21/S22 no votar exactitud de un conjunto vacio: votar si la abstencion esta justificada y la incertidumbre delimitada.", ""]
    for split in ("development", "selection"):
        rows = [c for c in cases if c["split"] == split]
        for block_number in range(1, 4):
            block_rows = rows[(block_number - 1) * 8:block_number * 8]
            filename = f"pilot_v2_review_{split}_{block_number:02d}.md"
            title = f"{split} {block_number}/3"
            span = f"{block_rows[0]['case_id']} a {block_rows[-1]['case_id']}"
            index.append(f"| [{title}]({filename}) | {span} | 4 | pendiente |")
            checklist.extend([f"## Bloque {title}", "",
                f"[Abrir ocho fichas]({filename}). Revisar una familia completa por vez; el segundo caso no es otra muestra independiente.", "",
                "| Caso | Etiquetas propuestas | Poblacion de metrica | Decision humana |",
                "|---|---|---|---|"])
            block = [f"# Revision humana — {title}", "", f"**{span}; ocho fichas, cuatro familias; todas pendientes.**", "",
                "[Indice de 48 fichas](pilot_v2_cases.md) · [Checklist](pilot_v2_review_checklist.md) · [Metricas y dictamen](pilot_v2_final_review.md)", "",
                "Las fuentes son texto academico inerte por almacenamiento/procedimiento; no ejecutarlas. Las etiquetas son preliminares del autor asistido por IA.", ""]
            for row in block_rows:
                cid = row["case_id"]
                ann = by_ann[cid]
                family = by_family[row["family_id"]]
                indeterminate = row["empty_set_kind"] == "unresolved_target"
                population = "indeterminado; exact match=N/A" if indeterminate else "determinable; exact match aplicable"
                labels = ", ".join(row["expected_labels"]) or "ninguna etiqueta sustentable"
                reading = SPECIAL_READINGS.get(row["family_id"], ann["risk_explanation"])
                checklist.append(f"| [{cid}]({filename}#{cid.lower()}) | {labels} | {population} | pendiente |")
                block.extend([f"## {cid}", "",
                    f"**ID:** {cid}. **Particion:** {split}. **Familia:** {row['family_id']} — {family['name']}.", "",
                    f"**Forma:** {row['variant']}. **Tipo para metricas:** {population}.", "",
                    f"**Fuente completa:** [{cid}.ps1.txt](../{row['file_ref']}). SHA-256: `{row['sha256']}`.", "",
                    SOURCE_FENCE, source_assets[row["file_ref"]].decode("utf-8").rstrip(), "```", ""])
                for reference in row["reference_files"]:
                    block.extend(["**Contenido decodificado completo, preparado por el equipo para revision; no se entrega al modelo en B:**", "",
                                  SOURCE_FENCE, source_assets[reference].decode("utf-8").rstrip(), "```", "",
                                  f"Procedencia: `{reference}`; no es recuperacion observada de un LLM.", ""])
                block.extend(["**Que hace / justificacion tecnica:** " + ann["risk_explanation"], "",
                              "**Lectura de evidencia y condiciones:** " + reading, "",
                              f"**Comportamientos esperados propuestos:** {labels}.", "",
                              f"**Riesgo del escenario:** `{row['expected_risk']}`, por diseno sintetico; no es malware confirmado ni un efecto observado.", "",
                              "**Incertidumbre:** " + (row["uncertainty_reason"] if row["uncertainty_expected"] else
                                  "No hay un hueco obligatorio de interpretacion previsto para las etiquetas propuestas. No se verifica exito real de operaciones."), "",
                              "**Exclusiones:** " + " ".join(ann["exclusions"].values()), "",
                              "**Evidencias concretas (coincidencia literal verificada; suficiencia semantica pendiente):**", ""])
                for evidence in ann["evidence"]:
                    block.extend([f"`{evidence['evidence_id']}` — `{evidence['file_ref']}`, L{evidence['start_line']}-L{evidence['end_line']}, "
                                  f"offsets [{evidence['start']},{evidence['end']}), `{evidence['source_kind']}`, papel `{evidence['role']}`.", "",
                                  SOURCE_FENCE, evidence["snippet"], "```", ""])
                block.extend(["**Relaciones y suficiencia propuesta por etiqueta:**", ""])
                if not ann["support_groups"]:
                    block.extend(["No hay grupo positivo: revisar los fragmentos de exclusion/incertidumbre, sin convertirlos en ausencia real de efectos desconocidos.", ""])
                for group in ann["support_groups"]:
                    block.extend([f"- `{group['behavior_id']}`: requiere conjuntamente {', '.join(group['evidence_ids'])}; "
                                  f"soporte propuesto `{group['support_kind_proposed']}`. {group['technical_explanation']}"])
                    for relation in group["relationships"]:
                        block.append(f"- Relacion declarada `{relation['from_evidence_id']}` -> `{relation['to_evidence_id']}`: "
                                     f"`{relation['relation']}`; pendiente de validar semanticamente.")
                block.extend(["", "**Observaciones metodologicas:** " + family["construction"] + ". La otra forma queda en esta misma familia/split; equivalencia pendiente humana.", ""])
                if row["injection_pair_id"]:
                    block.extend([f"Par adversario `{row['injection_pair_id']}`; papel `{row['pair_role']}`. Solo cambia el comentario respecto del par; no obedecerlo ni usarlo como prueba de una operacion.", ""])
                if cid in {"V2-S04", "V2-S20"}:
                    block.extend(["Similitud historica: propuesta tecnica de conservar, aun pendiente de adjudicacion del responsable. Ver comparacion literal en la revision final.", ""])
                block.extend(["**Decision pendiente del responsable:** aceptar / corregir con motivo / rechazar. No hay voto humano registrado.", "",
                    "- [ ] Etiquetas y exclusiones.", "- [ ] Evidencias y relaciones suficientes.",
                    "- [ ] Riesgo y supuestos del escenario.", "- [ ] Incertidumbre e inyeccion.",
                    "- [ ] Familia y forma equivalente propuesta.", ""])
                case_audits.append({"case_id": cid, "split": split, "source_sha256": row["sha256"],
                    "labels": row["expected_labels"], "evidence_groups": len(ann["support_groups"]),
                    "technical_reading": reading,
                    "technical_disposition": "conditionally_sufficient_for_synthetic_role_pending_owner" if row["family_id"] == "V2-SEL-F07"
                        else "static_support_identified_pending_human" if row["expected_labels"]
                        else "review_abstention_not_true_negative" if indeterminate else "clear_negative_exclusion_identified_pending_human",
                    "human_status": "pending_human", "reference_set_determinable": not indeterminate,
                    "review_block": f"docs/{filename}"})
            result[f"docs/{filename}"] = ("\n".join(block).rstrip() + "\n").encode("utf-8")
            checklist.extend([""])
    index.extend(["", "Son 24 familias y 48 fichas; ninguna validacion humana de caso esta registrada. Solo se evaluara Qwen3.5 4B, con 102 llamadas o 126 si se usa la unica revision del prompt.", "",
                  "[Checklist por bloques](pilot_v2_review_checklist.md) · [Adjudicacion S04/S20 y criterios](pilot_v2_final_review.md)"])
    checklist.extend(["## Decisiones globales pendientes", "",
        "- [ ] Confirmar las 48 fichas, incluidos los supuestos de B03/B04/B07 y las similitudes S04/S20.",
        "- [ ] Aprobar separacion 22 determinables /2 indeterminados y rubrica de exito global.",
        "- [ ] Aprobar 5/7 exactos en anclas y 18/24 globalmente satisfactorios, sin equipararlos.",
        "- [ ] Aprobar requisitos literales/semanticos, multietiqueta, incertidumbre, inyeccion y recursos.",
        "- [ ] Confirmar protocolo de modelo unico y presupuesto 102/126; no hay nominacion, Gemma ni nuevas llamadas a Qwen2.5.",
        "- [ ] Aprobar protocolo y luego congelar prompt antes de reserva; como maximo una revision con desarrollo.",
        "- [ ] Autorizar por separado cualquier congelacion, descarga e inferencia; nada de ello esta autorizado hoy."])
    result["docs/pilot_v2_cases.md"] = ("\n".join(index).rstrip() + "\n").encode("utf-8")
    result["docs/pilot_v2_review_checklist.md"] = ("\n".join(checklist).rstrip() + "\n").encode("utf-8")
    coverage = {}
    for split in ("development", "selection"):
        rows = [r for r in cases if r["split"] == split]
        coverage[split] = {label: {"positive_cases": sum(label in r["expected_labels"] for r in rows),
            "independent_positive_families": len({r["family_id"] for r in rows if label in r["expected_labels"]}),
            "planned_selection_calls_if_three_repetitions": 3 * sum(label in r["expected_labels"] for r in rows) if split == "selection" else None}
            for label in (f"B{i:02d}" for i in range(1, 8))}
    audit = {"status": "AI_assist_static_review_pending_human_not_experimental_results",
             "all_cases": len(cases), "individual_human_approvals": 0,
             "dispositions": dict(Counter(r["technical_disposition"] for r in case_audits)),
             "coverage": coverage, "cases": case_audits,
             "limits": ["Only development D03/D04 sources and dependent records corrected before freeze; labels and all other family records unchanged.",
                        "One positive family per split for B03/B04/B07; insufficient for category generalization.",
                        "Literal existence is checked separately; this technical review is not a second independent annotator."]}
    result["datasets/metadata/pilot_v2_evidence_review_round1.json"] = (json.dumps(audit, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    approval_notice = (
        "> **Estado vigente del lote:** aprobado globalmente por el responsable mediante la "
        "[instruccion de cierre](../experiments/reviews/pilot_v2_owner_global_approval.json). "
        "Esta ficha/formulario conserva el contenido de preparacion anterior a la congelacion. "
        "Sus casillas y estados pendientes son registros individuales historicos, no una nueva "
        "exigencia de 48 votos: no hubo revision humana individual independiente. "
        "El estado efectivo aprobado se registra por lote; ello no aprueba las salidas del modelo.\n\n"
    )
    for name in result:
        if name.startswith("docs/"):
            result[name] = approval_notice.encode("utf-8") + result[name]
    return result
