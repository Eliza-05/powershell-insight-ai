"""Build a self-contained HTML form for Karol's PERSONAL review of the 16 Phase 4 references.

Runs on the VM next to the candidate. The agent never opens the output: it only contains data
already in the candidate (cases.json, scripts, reference_review.template.json). The page lets the
reviewer read every script as text, record a decision and notes per case and download the review
JSON in the exact schema `Proposal.seal` validates. Nothing is approved by default.
Usage: python make_reference_review_page.py <artifacts/phase4_preparation> <out.html>
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path

LABELS = {"B01": "Descarga remota", "B02": "Ejecución dinámica de código", "B03": "Persistencia",
          "B04": "Debilitar defensas/registro", "B05": "Reconocimiento del sistema",
          "B06": "Comunicación de red (no descarga)", "B07": "Acceso a credenciales"}


def esc(value):
    return html.escape(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=1))


def main(out_dir, target):
    out = Path(out_dir)
    plan = out / "proposal"
    cases = json.loads((plan / "cases.json").read_text(encoding="utf-8"))["cases"]
    template = json.loads((out / "reference_review.template.json").read_text(encoding="utf-8"))
    audit = json.loads((plan / "independence_audit.json").read_text(encoding="utf-8"))
    manifest_sha = hashlib.sha256((out / "CANDIDATE_MANIFEST.json").read_bytes()).hexdigest()
    assert template["candidate_sha256"] == manifest_sha, "template not bound to current candidate"
    rows = {r["id"]: r for r in template["case_reviews"]}
    audit_by_id = {c.get("id"): c for c in audit.get("cases", []) if isinstance(c, dict)}
    blocks = []
    for c in cases:
        script = (plan / c["script_file"]).read_text(encoding="utf-8")
        r = rows[c["id"]]
        labels = c["expected_labels"]
        shown = "INDETERMINADA (null)" if labels is None else (", ".join(f"{l} {LABELS[l]}" for l in labels) or "Conjunto vacío (sin comportamientos)")
        blocks.append(f"""
<section class="case" data-id="{esc(c['id'])}">
<h2>{esc(c['id'])} — {esc(c.get('title', ''))}</h2>
<p class="meta">Escenario: {esc(c.get('scenario_type', ''))} · Estrato de recuperación: {esc(c.get('recovery_stratum', ''))} · Bloque: {esc(c.get('cluster', ''))}<br>
script_sha256 <code>{esc(c['script_sha256'])}</code> · reference_sha256 <code>{esc(r['reference_sha256'])}</code></p>
<h3>Script (solo texto; no ejecutar)</h3><pre class="script">{esc(script)}</pre>
<h3>Referencia propuesta</h3>
<p class="ref"><b>Etiquetas esperadas:</b> {esc(shown)}</p>
<p><b>Justificación de inclusión:</b> {esc(c.get('inclusion_rationale', ''))}</p>
<p><b>Justificación de ausencias:</b> {esc(c.get('absent_rationale', ''))}</p>
<details><summary>Evidencia de referencia localizada en el original</summary><pre>{esc(c.get('reference_evidence_located', []))}</pre></details>
<details><summary>Exclusiones por etiqueta, conocidos presentes/ausentes, fragmentos desconocidos requeridos</summary>
<pre>{esc({k: c.get(k) for k in ('exclusion_rationales_by_label', 'known_present', 'known_absent', 'required_unknown_fragments', 'reference_state')})}</pre></details>
<details><summary>Recuperación 1A verificada (lo que verá el modo C)</summary><pre>{esc({k: c.get(k) for k in ('recovery_status', 'verified_1A_sources', 'unresolved_1A', 'expected_recovered_strings')})}</pre></details>
<details><summary>Novedad, independencia y seguridad propuestas</summary><pre>{esc({k: c.get(k) for k in ('novel_logic', 'independence_status', 'safety')})}
Auditoría automática: {esc(audit_by_id.get(c['id'], 'ver independence_audit.json'))}</pre></details>
<div class="decision">
<label><input type="radio" name="d_{esc(c['id'])}" value="approve"> Apruebo esta referencia</label>
<label><input type="radio" name="d_{esc(c['id'])}" value="reject"> No la apruebo / requiere corrección</label>
<textarea placeholder="Observaciones (obligatorio si no apruebas; recomendado siempre)" data-notes="{esc(c['id'])}"></textarea>
</div></section>""")
    page = f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Revisión personal de referencias F4</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--bg:#fafaf7;--fg:#1d1d1b;--mut:#666;--card:#fff;--line:#ddd;--acc:#1f5fbf}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151515;--fg:#eee;--mut:#aaa;--card:#1e1e1e;--line:#333;--acc:#7fb0ff}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:980px;margin:0 auto;padding:16px}}
.case{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:18px 0}}
pre{{white-space:pre-wrap;word-break:break-word;background:rgba(127,127,127,.1);padding:10px;border-radius:6px;font-size:13px}}
.script{{max-height:420px;overflow:auto}} .meta{{color:var(--mut);font-size:13px}} code{{font-size:12px}}
.decision label{{display:block;margin:4px 0}} textarea{{width:100%;min-height:60px;margin-top:6px;background:transparent;color:var(--fg);border:1px solid var(--line);border-radius:6px}}
.final{{position:sticky;bottom:0;background:var(--card);border:2px solid var(--acc);border-radius:10px;padding:12px 16px}}
button{{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:15px;cursor:pointer}} #msg{{color:#c33}}
</style></head><body>
<h1>Revisión personal de las 16 referencias F4</h1>
<p>Candidato <code>{manifest_sha}</code>. Esta página la generó el código a partir del candidato; nada viene aprobado. Lee cada script como texto, contrasta la referencia con la taxonomía B01–B07 y decide. Si no apruebas alguna, el FREEZE no se puede sellar (hay que corregir y versionar el candidato).</p>
<p><b>Taxonomía:</b> {' · '.join(f'{k} {v}' for k, v in LABELS.items())}. Las dos indeterminadas deben quedar como <i>null</i>, no como vacías.</p>
<p><b>Auditoría automática de independencia:</b> duplicado exacto o de programa encontrado: {esc(str(audit.get('automatic_exact_or_program_duplicate_found')))}. {esc(audit.get('algorithm', ''))}</p>
{''.join(blocks)}
<div class="final">
<label>Nombre completo de la revisora: <input id="reviewer" size="30"></label><br>
<label><input type="checkbox" id="ra"> Apruebo las 16 referencias tal como están</label><br>
<label><input type="checkbox" id="si"> Apruebo la independencia semántica de los casos (respecto de los datos de desarrollo)</label><br>
<label><input type="checkbox" id="sa"> Apruebo la seguridad de los textos (no son muestras ejecutables reales)</label><br>
<button id="dl">Descargar revisión (JSON)</button> <span id="msg"></span>
</div>
<script>
const TEMPLATE = {json.dumps(template, ensure_ascii=False)};
function tzIso(d){{const p=n=>String(n).padStart(2,'0');const o=-d.getTimezoneOffset();const s=o>=0?'+':'-';const a=Math.abs(o);
return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+'T'+p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds())+s+p(Math.floor(a/60))+':'+p(a%60);}}
document.getElementById('dl').onclick=()=>{{
  const msg=document.getElementById('msg'); msg.textContent='';
  const reviewer=document.getElementById('reviewer').value.trim();
  const out=JSON.parse(JSON.stringify(TEMPLATE)); let missing=[];
  out.case_reviews.forEach(r=>{{const d=document.querySelector('input[name="d_'+r.id+'"]:checked');
    const n=document.querySelector('textarea[data-notes="'+r.id+'"]').value.trim();
    if(!d) missing.push(r.id); r.approved = !!d && d.value==='approve'; r.notes=n;
    if(d && d.value==='reject' && !n) missing.push(r.id+' (falta observación)');}});
  if(!reviewer) missing.push('nombre');
  if(missing.length){{msg.textContent='Falta decidir: '+missing.join(', ');return;}}
  const allOk=out.case_reviews.every(r=>r.approved);
  out.reviewer=reviewer; out.reviewed_at=tzIso(new Date());
  out.references_approved=document.getElementById('ra').checked && allOk;
  out.semantic_independence_approved=document.getElementById('si').checked;
  out.safety_approved=document.getElementById('sa').checked;
  const blob=new Blob([JSON.stringify(out,null,2)+'\\n'],{{type:'application/json'}});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='revision_referencias_F4_Karol.json'; a.click();
  if(!allOk) msg.textContent='Descargado. Hay casos no aprobados: el FREEZE no podrá sellarse hasta corregirlos.';
}};
</script></body></html>"""
    Path(target).write_text(page, encoding="utf-8")
    print("ok", len(cases), "casos", hashlib.sha256(page.encode()).hexdigest())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
