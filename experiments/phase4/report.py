"""Human-readable proposal material from exact scripts and pending references."""
from __future__ import annotations

from pathlib import Path

from experiments.phase4.common import ROOT, OUT, load, digest, save, now


def execution_document(value, path):
    """Derived report tied to the immutable evaluation JSON; no output repair."""
    lines = ["# Fase 4 — reporte de la ejecución registrada", "",
        f"Fuente reproducible: `{path.with_suffix('.json').name}`. Estado operativo completo: **{value['operationally_complete']}**.",
        f"Resultados registrados: {value['recorded_results']}/48; parejas completas: {value['recorded_pairs']}/16.",
        "La finalización operativa no implica calidad suficiente ni aprobación de hipótesis.", "",
        "| Modo | TP | FP | FN | Precisión micro | Recall micro | F1 micro |", "|---|---:|---:|---:|---:|---:|---:|"]
    for mode in ("A", "B", "C"):
        m = value["classification"][mode]["micro"]
        lines.append(f"| {mode} | {m['TP']} | {m['FP']} | {m['FN']} | {m['precision']} | {m['recall']} | {m['F1']} |")
    lines += ["", "Cobertura A: " + repr(value["A_coverage"]),
        "Los rechazos no se convierten en conjuntos vacíos exitosos. La coincidencia matemática de A se informa junto con su cobertura calificada; parcial no certifica benignidad.", "",
        "## Hipótesis y revisión", "", "H1: " + repr(value["H1"]), "", "H2: " + repr(value["H2"]), "",
        "Ninguna hipótesis se acepta automáticamente. Los p condicionales y sus supuestos no demuestran representatividad, significación poblacional ni causalidad general.", "",
        "## Resultados por unidad y modo", "", "| Unidad | Modo | Estado | Referencia | Predicción admitida |", "|---|---|---|---|---|"]
    for row in value["rows"]:
        lines.append(f"| {row['unit']} | {row['mode']} | {row['status']} | {row['expected']} | {row['predicted']} |")
    lines += ["", "Los hashes, citas crudas, procedencia, reconstrucciones, riesgo/incertidumbre, macro métricas, estratos y pasos no ejecutados se conservan en el JSON fuente. No se sustituyeron respuestas históricas ni se corrigió el contenido del modelo."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def documents():
    plan = OUT / "proposal"
    cases = load(plan / "cases.json")["cases"]
    lines = ["# Fase 4 — referencias propuestas de los 16 textos", "",
        "**Pendientes de revisión personal y de congelación aprobada. Cero inferencias nuevas.**",
        "No se usaron predicciones B/C ni etiquetas 1B para construir estas propuestas. Los resultados 1A verifican recuperación textual, no las referencias semánticas.", "",
        "| ID | Escenario | Referencia propuesta | Recuperación 1A | Estado de referencia |", "|---|---|---|---|---|"]
    for case in cases:
        labels = "+".join(case["expected_labels"]) if case["expected_labels"] else ("[]" if case["expected_labels"] == [] else "Indeterminado")
        lines.append(f"| [{case['id']}](../artifacts/phase4_preparation/review_packets/{case['id']}.md) | {case['title']} | {labels} | {'No vacía' if case['verified_1A_sources'] else 'Sin texto verificado relevante'} | {case['reference_state']} |")
        script = (plan / case["script_file"]).read_text(encoding="utf-8")
        packet = [f"# {case['id']} — {case['title']}", "", "**Propuesta de IA; revisión personal pendiente. No ejecutar este texto.**", "",
            f"SHA-256: `{case['script_sha256']}`. Archivo `.ps1.txt`: `{case['script_file']}`.", "",
            "## Texto exacto", "", "```text", script.rstrip(), "```", "",
            "## Referencia propuesta", "", f"Etiquetas: `{case['expected_labels']}`. Estado: `{case['reference_state']}`.",
            f"Conocidas al menos: `{case['known_present']}`. Fragmentos desconocidos: `{case['required_unknown_fragments']}`.", "",
            "### Inclusiones", ""]
        packet += [f"- {label}: {reason}" for label, reason in case["inclusion_rationale"].items()] or ["Sin etiquetas funcionales propuestas."]
        packet += ["", "### Exclusiones y ausencias", "", case["absent_rationale"], "",
            f"Excluidas del conjunto determinable: `{case['excluded_labels']}`; las indeterminadas no reciben un conjunto vacío ficticio.", "",
            "### Evidencias de referencia", ""]
        packet += [f"- Exclusión {label}: {reason}" for label, reason in case["exclusion_rationales_by_label"].items()]
        packet += [f"- {v['behavior_id']}, original L{v['line']}, fragmento `{v['snippet']}`. Soporte propuesto contextual; aún no adjudicado." for v in case["reference_evidence_located"]]
        packet += ["", "## Recuperación 1A y activación", "", f"Estado 1A: `{case['recovery_status']}`.",
            "Texto esperado por diseño: " + repr(case["expected_recovered_strings"]), "",
            "Fuentes verificadas realmente suministrables a C:", ""]
        for sid, text in case["verified_1A_sources"].items(): packet += [f"### {sid}", "", "```text", text, "```", ""]
        packet += ["La recuperación no prueba invocación. Revisar el enlace entre fuente, operación, alcance y llamada en el original.", "",
            "## Independencia y seguridad", "", case["novel_logic"], "", f"Bloque estadístico conservador: `{case['cluster']}`.", "",
            case["safety"], "", "## Revisión personal requerida", "",
            "Confirmar o corregir inclusiones, exclusiones, indeterminación, fragmentos, activación, novedad semántica y seguridad ANTES de congelar. Una modificación exige una nueva versión candidata; no editar después de ver respuestas B/C."]
        path = OUT / "review_packets" / (case["id"] + ".md")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(packet) + "\n", encoding="utf-8")
    lines += ["", "## Cobertura propuesta", "", "| Comportamiento | Unidades determinables positivas |", "|---|---|"]
    for label in [f"B{i:02}" for i in range(1, 8)]:
        lines.append(f"| {label} | {', '.join(c['id'] for c in cases if c['expected_labels'] is not None and label in c['expected_labels'])} |")
    lines += ["", "Dos unidades tienen conjunto completo indeterminado y se mantienen fuera de los denominadores de clasificación: F4-15 (sin etiquetas conocidas) y F4-16 (B05 conocida como mínimo, callback desconocido). Se evalúa la abstención/incertidumbre por separado.", "",
        "Ocho textos tienen recuperación no vacía; ocho no. Los mecanismos de logging F4-04/F4-10 comparten bloque estadístico conservador `audit-control`: 16 textos, 15 bloques, 13 bloques entre los 14 determinables. Esta agrupación no convierte los restantes en una muestra aleatoria de una población.", "",
        "La revisión de novedad debe consultar el [audit estructural y sus coincidencias más cercanas](../artifacts/phase4_preparation/proposal/independence_audit.json). Compartir una primitiva B01–B07 es inevitable; renombrarla no demuestra independencia."]
    (ROOT / "docs/phase4_references_proposed.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    audit = load(plan / "independence_audit.json")
    review = ["# Fase 4 — independencia: evidencia y revisión pendiente", "",
        "**Ninguna referencia o independencia semántica está aprobada automáticamente.**", "",
        f"Audit local: {audit['prior_unique_exact_texts']} textos previos únicos y {audit['prior_unique_normalized_views']} vistas estructurales únicas. Cero duplicados exactos o programas completos normalizados equivalentes encontrados.", "",
        "El inventario se limita a archivos presentes en el manifiesto anterior a esta preparación. Incluye selección, desarrollo, diagnósticos y literales de pruebas; excluye los nuevos tests Fase 4 y los borradores para evitar autocontaminación del audit. No se leyeron muestras raw, externas, privadas o en cuarentena.", "",
        "Se ignoran comentarios y se normalizan variables, strings y números. También se inspeccionan vistas de texto recuperadas determinísticamente para no ocultar un base antiguo bajo otro wrapper. Los scores de secuencia de tokens son cribado, no equivalencia semántica.", "",
        "| ID | Prior más cercano | Similitud estructural | Diferencia lógica propuesta por el autor; pendiente de revisión |", "|---|---|---:|---|"]
    for item in audit["cases"]:
        closest = item["nearest_prior_programs"][0]
        review.append(f"| {item['id']} | `{closest['origin']}` | {closest['token_similarity']:.3f} | {item['novel_logic_author_rationale']} |")
    review += ["", "## Puntos que debe revisar personalmente el responsable", "",
        "- F4-08 inicialmente repetía el patrón exterior de ScriptBlock.Create de V2-S04 (0,939). Antes de cualquier respuesta B/C se sustituyó por generación de IL, ejecución de una suma local y una relación de datos distinta. El nuevo vecino más próximo tiene similitud 0,318. Los borradores anteriores se conservaron; no son parte del candidato actual.",
        "- F4-04 comparte el esqueleto asignación/concatenación con un demo previo que solo mostraba texto; la operación nueva es Clear-EventLog remoto. Confirmar que esa diferencia es funcional, no solo nominal.",
        "- F4-12 comparte Get-Credential con controles anteriores, pero enlaza la credencial a remoting y no a un proceso local o mera solicitud. Confirmar el nuevo flujo y la exclusión B07.",
        "- F4-02/F4-05 comparten construcción de URL y WebClient; el primero descarga bytes y carga un ensamblado, el segundo consulta eventos y envía su JSON por PUT. Revisar posible dependencia residual, sin asumir independencia por API distinta.",
        "- F4-06/F4-07 comparten asignación de texto, pero difieren entre lectura material de credencial CLIXML y compilación almacenada nunca invocada. La similitud léxica por boilerplate no decide por sí sola la familia.",
        "- Los dos mecanismos de logging F4-04/F4-10 se agruparon conservadoramente en audit-control. Otras agrupaciones solo pueden cambiarse antes de congelar, con justificación personal.", "",
        "## Límites", "",
        "No es posible demostrar independencia lógica completa mediante hash o normalización. Las referencias y la novedad deben revisarse personalmente antes de sellar. Los mismos autores conocían los fallos históricos, las primitivas B01–B07 siguen siendo compartidas y el corpus no es una muestra aleatoria. No se afirma independencia del preentrenamiento de Qwen ni generalización a malware real.", "",
        "El archivo [independence_audit.json](../artifacts/phase4_preparation/proposal/independence_audit.json) conserva los tres vecinos más cercanos por caso y las banderas de similitud interna. Las observaciones de este documento son asistidas por IA y no constituyen una revisión humana independiente."]
    (ROOT / "docs/phase4_independence_review.md").write_text("\n".join(review) + "\n", encoding="utf-8")
    print("16 review packets and reference table generated; no personal approvals assigned")


if __name__ == "__main__": documents()
