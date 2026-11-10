"""Build a self-contained HTML form for Karol's PERSONAL H2 claim review of all B/C outputs.

Runs on the VM after the campaign. The agent never opens the output. For each B/C result it shows
the script (text only), the verified 1A sources visible to C, the raw model output, and a claim
inventory PRE-SEGMENTED mechanically by field (one row per explanation, reconstruction, risk
rationale, uncertainty note, limitation...). Pre-segmentation is not adjudication: every support
category starts empty, the reviewer can edit/split/add/delete claims, and must confirm the
inventory is complete. One download holds all reviews; `split_h2_reviews.py` writes the
per-output files that `experiments.phase4 evaluate --personal-reviews` validates.
Usage: python make_h2_review_page.py <artifacts/phase4_preparation> <out.html>
"""
from __future__ import annotations

import hashlib
import html
import json
import sys
from pathlib import Path


def esc(v):
    return html.escape(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, indent=1))


def segment(raw):
    """Mechanical field-level segmentation of a raw ModelReport. No judgement of support."""
    try:
        r = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(r, dict):
        return None
    out = []
    def add(field, text):
        if isinstance(text, str) and text.strip() and text in raw:
            out.append({"field": field, "quote": text})
    for b in r.get("behaviors") or []:
        if isinstance(b, dict):
            add(f"behaviors[{b.get('behavior_id')}].explanation", b.get("explanation"))
    for i, t in enumerate(r.get("recovered_content") or []):
        add(f"recovered_content[{i}]", t)
    add("risk_rationale", r.get("risk_rationale"))
    u = r.get("uncertainty") or {}
    add("uncertainty.notes", u.get("notes") if isinstance(u, dict) else None)
    for i, t in enumerate((u.get("uninterpretable_fragments") if isinstance(u, dict) else None) or []):
        add(f"uncertainty.uninterpretable_fragments[{i}]", t)
    pi = r.get("prompt_injection") or {}
    add("prompt_injection.notes", pi.get("notes") if isinstance(pi, dict) else None)
    for i, t in enumerate(r.get("limitations") or []):
        add(f"limitations[{i}]", t)
    return out


def main(out_dir, target):
    out = Path(out_dir)
    plan = out / "proposal"
    cases = {c["id"]: c for c in json.loads((plan / "cases.json").read_text(encoding="utf-8"))["cases"]}
    order = json.loads((plan / "order.json").read_text(encoding="utf-8"))["sequence"]
    items = []
    for step in order:
        if step["mode"] == "A":
            continue
        key = f"{step['unit']}-{step['mode']}"
        path = out / "execution/results" / (key + ".json")
        if not path.exists():
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        pipe = record["pipeline"]
        raw = pipe.get("operational", {}).get("response", {}).get("message", {}).get("content", "") or ""
        c = cases[step["unit"]]
        items.append({"key": key, "unit": step["unit"], "mode": step["mode"],
            "result_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "output_started_at": pipe.get("started_at"), "status": pipe.get("status"),
            "errors": [e.get("code") for e in pipe.get("errors", [])],
            "script": (plan / c["script_file"]).read_text(encoding="utf-8"),
            "sources_C": c.get("verified_1A_sources") if step["mode"] == "C" else {},
            "accepted": [b.get("behavior_id") for b in (pipe.get("llm") or {}).get("behaviors", [])] if pipe.get("llm") else None,
            "raw": raw, "segments": segment(raw)})
    data = json.dumps(items, ensure_ascii=False)
    page = """<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Revisión H2 de afirmaciones</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--mut:#666;--card:#fff;--line:#ddd;--acc:#1f5fbf;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#151515;--fg:#eee;--mut:#aaa;--card:#1e1e1e;--line:#333;--acc:#7fb0ff;--bad:#ff8a80}}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:1100px;margin:0 auto;padding:16px}
.out{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:18px 0}
pre{white-space:pre-wrap;word-break:break-word;background:rgba(127,127,127,.1);padding:10px;border-radius:6px;font-size:13px;max-height:340px;overflow:auto}
.claim{border-top:1px dashed var(--line);padding:8px 0} .claim textarea,.claim input[type=text]{width:100%;background:transparent;color:var(--fg);border:1px solid var(--line);border-radius:6px}
.meta{color:var(--mut);font-size:13px} .done{color:green} .todo{color:var(--bad)} button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:6px 12px;cursor:pointer}
.small{font-size:12px;padding:3px 8px} nav{position:sticky;top:0;background:var(--bg);padding:6px 0;z-index:2} nav a{margin-right:6px;font-size:13px}
.final{position:sticky;bottom:0;background:var(--card);border:2px solid var(--acc);border-radius:10px;padding:12px 16px}
</style></head><body>
<h1>Revisión personal H2: afirmaciones de las salidas B y C</h1>
<p>Para cada salida cruda del modelo, la herramienta separó mecánicamente las afirmaciones por campo (explicaciones, reconstrucciones, riesgo, incertidumbre, limitaciones). <b>No juzgó nada:</b> la categoría está vacía. Puedes editar la proposición, dividir/añadir/eliminar afirmaciones (la cita debe ser texto literal de la salida). Categorías estrictas:
<b>individual</b> (la afirmación está respaldada por una cita/fuente concreta), <b>contextual_cited</b> (respaldada por el contexto citado), <b>insufficient</b> (no hay respaldo suficiente en el script/recuperación), <b>contradicted</b> (el script/recuperación la contradice), <b>unassessable</b> (no se puede evaluar; evita usarla: invalida la salida para H2).</p>
<nav id="nav"></nav><div id="outs"></div>
<div class="final">Revisora: <input id="reviewer" size="28"> <span id="prog"></span>
<button id="dl">Descargar revisión H2 (JSON)</button> <span id="msg" class="todo"></span></div>
<script>
const ITEMS = __DATA__;
const CATS=['','individual','contextual_cited','insufficient','contradicted','unassessable'];
const el=(t,a={},...k)=>{const e=document.createElement(t);Object.assign(e,a);k.forEach(x=>e.append(x));return e};
const state={};
function claimRow(it,c){const box=el('div',{className:'claim'});
 const q=el('textarea',{value:c.quote,rows:2}); const p=el('textarea',{value:c.proposition||c.quote,rows:2});
 const s=el('select'); CATS.forEach(v=>s.append(el('option',{value:v,textContent:v||'— categoría estricta —'}))); s.value=c.strict||'';
 const perm=el('input',{type:'checkbox',checked:!!c.permissive}); const src=el('input',{type:'text',value:(c.sources||[]).join(', '),placeholder:'fuentes (original, T0001...)'});
 const rat=el('textarea',{value:c.rationale||'',rows:2,placeholder:'Justificación (obligatoria)'}); const del=el('button',{className:'small',textContent:'Eliminar'});
 del.onclick=()=>{box.remove();upd()}; [q,p,s,perm,src,rat].forEach(x=>x.oninput=x.onchange=upd);
 box.append(el('div',{className:'meta',textContent:c.field||'añadida por la revisora'}),'Cita literal:',q,'Proposición:',p,s,' ',el('label',{},perm,' apoyo permisivo por contexto'),src,rat,del);
 box.get=()=>({quote:q.value,proposition:p.value.trim(),strict_support:s.value,permissive_context_support:perm.checked,
   source_ids:src.value.split(',').map(x=>x.trim()).filter(Boolean),rationale:rat.value.trim()}); return box}
ITEMS.forEach((it,i)=>{const sec=el('section',{className:'out',id:'o'+i});
 sec.append(el('h2',{textContent:it.key+' ('+it.status+(it.errors.length?' · '+it.errors.join(','):'')+')'}),
  el('p',{className:'meta',textContent:'result_sha256 '+it.result_sha256+' · etiquetas publicadas: '+JSON.stringify(it.accepted)}),
  el('details',{},el('summary',{textContent:'Script (solo texto; no ejecutar)'}),el('pre',{textContent:it.script})));
 if(it.mode==='C') sec.append(el('details',{},el('summary',{textContent:'Recuperación 1A verificada (fuentes de C)'}),el('pre',{textContent:JSON.stringify(it.sources_C,null,1)})));
 sec.append(el('details',{open:true},el('summary',{textContent:'Salida cruda del modelo'}),el('pre',{textContent:it.raw||'(vacía)'})));
 const list=el('div'); (it.segments||[]).forEach(c=>list.append(claimRow(it,c)));
 if(it.segments===null) sec.append(el('p',{className:'todo',textContent:'La salida no es JSON legible: añade las afirmaciones a mano (o márcalas unassessable si no se puede).'}));
 const add=el('button',{className:'small',textContent:'Añadir afirmación'}); add.onclick=()=>{list.append(claimRow(it,{quote:'',proposition:''}));upd()};
 const inv=el('input',{type:'number',min:0,value:''}), alt=el('input',{type:'number',min:0,value:''});
 const notes=el('textarea',{rows:2,placeholder:'Notas sobre riesgo/incertidumbre (obligatorio)'}); const comp=el('input',{type:'checkbox'});
 [inv,alt,notes,comp].forEach(x=>x.oninput=x.onchange=upd);
 sec.append(el('h3',{textContent:'Afirmaciones'}),list,add,el('p',{},'Reconstrucciones inventadas: ',inv,' · alteradas: ',alt),notes,
  el('p',{},el('label',{},comp,' Confirmo que el inventario de afirmaciones de esta salida está completo')));
 state[it.key]={it,list,inv,alt,notes,comp}; document.getElementById('outs').append(sec);
 document.getElementById('nav').append(el('a',{href:'#o'+i,id:'n'+i,textContent:it.key}))});
function check(k){const s=state[k];const cl=[...s.list.children].map(b=>b.get());const e=[];
 if(!cl.length)e.push('sin afirmaciones');
 cl.forEach((c,j)=>{if(!c.quote.trim()||!s.it.raw.includes(c.quote))e.push('cita '+(j+1)+' no literal');if(!c.proposition)e.push('proposición '+(j+1));
  if(!c.strict_support)e.push('categoría '+(j+1));if(!c.rationale)e.push('justificación '+(j+1))});
 const props=cl.map(c=>c.proposition.toLowerCase()); if(new Set(props).size!==props.length)e.push('proposiciones repetidas');
 if(s.inv.value===''||s.alt.value==='')e.push('reconstrucciones'); if(!s.notes.value.trim())e.push('notas'); if(!s.comp.checked)e.push('confirmar inventario');
 return {cl,e}}
function upd(){let ok=0;ITEMS.forEach((it,i)=>{const r=check(it.key);document.getElementById('n'+i).className=r.e.length?'todo':'done';if(!r.e.length)ok++});
 document.getElementById('prog').textContent=ok+' / '+ITEMS.length+' salidas completas'} upd();
function tzIso(d){const p=n=>String(n).padStart(2,'0');const o=-d.getTimezoneOffset();const s=o>=0?'+':'-';const a=Math.abs(o);
 return d.getFullYear()+'-'+p(d.getMonth()+1)+'-'+p(d.getDate())+'T'+p(d.getHours())+':'+p(d.getMinutes())+':'+p(d.getSeconds())+s+p(Math.floor(a/60))+':'+p(a%60)}
document.getElementById('dl').onclick=()=>{const reviewer=document.getElementById('reviewer').value.trim();const msg=document.getElementById('msg');
 if(!reviewer){msg.textContent='Falta el nombre';return} const at=tzIso(new Date()); const out={reviewer,saved_at:at,reviews:{}};let pend=[];
 ITEMS.forEach(it=>{const r=check(it.key); if(r.e.length){pend.push(it.key);return}
  out.reviews[it.key]={unit:it.unit,mode:it.mode,result_sha256:it.result_sha256,reviewer_type:'human_personal',human_confirmed:true,reviewer,reviewed_at:at,
   inventory_complete:true,invented_reconstructions:parseInt(state[it.key].inv.value),altered_reconstructions:parseInt(state[it.key].alt.value),
   risk_uncertainty_notes:state[it.key].notes.value.trim(),claims:r.cl.map((c,j)=>Object.assign({claim_id:'CL'+String(j+1).padStart(2,'0')},c))}});
 const b=new Blob([JSON.stringify(out,null,1)+'\\n'],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);
 a.download='revision_H2_Karol.json';a.click(); msg.textContent=pend.length?('Descargado parcial. Pendientes: '+pend.join(', ')):'Descargado: todas completas.'};
</script></body></html>""".replace("__DATA__", data.replace("</", "<\\/"))
    Path(target).write_text(page, encoding="utf-8")
    print("ok", len(items), "salidas", hashlib.sha256(page.encode()).hexdigest())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
