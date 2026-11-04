"""Post-hoc descriptive reporting only; never dispatches inference requests."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree

from experiments.qwen14_campaign import OUT, ROOT, Protocol, load, write, evaluate, rates
from experiments.qwen14_environment import sha, now

GIB=1024**3


def artifacts():
    p=Protocol()
    if not (OUT/"evaluation.json").exists():
        evaluate()
    evaluation=load(OUT/"evaluation.json")
    records=[load(path) for path in sorted((OUT/"execution/results").glob("*.json"))]
    all_samples=[]
    for row,record in zip(evaluation["rows"],records):
        call=next(c for c in p.calls if c["call_id"]==row["call_id"])
        op=record["pipeline"]["operational"]
        raw=op.get("response",{}).get("message",{}).get("content","")
        all_samples.extend(op.get("resources",{}).get("samples",[]))
        path=OUT/"review_packets"/(row["call_id"]+".md")
        path.parent.mkdir(parents=True,exist_ok=True)
        text=f"# {row['call_id']} — revisión personal pendiente\n\n"
        text+=f"Modo {row['mode']}; desarrollo reutilizado de {call['gemma_equivalent']}.\n\n"
        text+=f"Resultado SHA-256: `{sha(OUT/'execution/results'/(row['call_id']+'.json'))}`.\n\n"
        text+="## Original (solo texto; nunca ejecutado)\n\n```powershell\n"+record["pipeline"]["original"]+"\n```\n\n"
        text+="## Fuentes disponibles al modelo\n\n```json\n"+json.dumps(call["sources_for_review_only"],ensure_ascii=False,indent=2)+"\n```\n\n"
        text+="## Respuesta cruda del intento nuevo\n\n```json\n"+raw+"\n```\n\n"
        text+="## Evaluación automática (no adjudicación semántica personal)\n\n```json\n"+json.dumps(row,ensure_ascii=False,indent=2)+"\n```\n"
        with path.open("x",encoding="utf-8") as f:f.write(text)
    summaries=[]
    for record in records:
        samples=record["pipeline"]["operational"].get("resources",{}).get("samples",[])
        for sample in samples:
            processes=[v for v in sample["processes"] if v.get("is_ollama_runtime")]
            summaries.append({"private":sum(v.get("private",0) for v in processes),
                "working_set":sum(v.get("working_set",0) for v in processes)})
    resource_summary={"sample_count":len(all_samples),
        "RAM_available_min_bytes":min((s["available_bytes"] for s in all_samples),default=None),
        "commit_available_min_bytes":min((s["commit_available_bytes"] for s in all_samples),default=None),
        "ollama_tree_private_peak_bytes":max((s["private"] for s in summaries),default=None),
        "ollama_tree_working_set_peak_bytes":max((s["working_set"] for s in summaries),default=None),
        "inference_seconds_total":sum(r.get("inference_seconds") or 0 for r in evaluation["rows"]),
        "prompt_tokens":sum(r["metrics"]["prompt_eval_count"] or 0 for r in evaluation["rows"]),
        "output_tokens":sum(r["metrics"]["eval_count"] or 0 for r in evaluation["rows"]),
        "margin_violations":sum(r["pipeline"]["operational"].get("resources",{}).get("margin_violated",False) for r in records),
        "measurement_limit":"Aggregated Ollama process tree, not exclusive model consumption; page faults include soft faults."}
    write(OUT/"resource_summary.json",resource_summary)
    by_label={}
    for label in [f"B{i:02}" for i in range(1,8)]:
        by_label[label]=rates(sum(label in (r["predicted"] or []) and label in r["expected"] for r in evaluation["rows"]),
            sum(label in (r["predicted"] or []) and label not in r["expected"] for r in evaluation["rows"]),
            sum(label not in (r["predicted"] or []) and label in r["expected"] for r in evaluation["rows"]))
    write(OUT/"per_label_metrics.json",by_label)
    comparisons=[]
    for call,record,row in zip(p.calls,records,evaluation["rows"]):
        old=load(ROOT/"artifacts/gemma4_development_v2/execution/results"/(call["gemma_equivalent"]+".json"))["pipeline"]
        oldraw=json.loads(old["operational"]["response"]["message"]["content"])
        oldsamples=old["operational"]["resources"]["samples"]
        comparisons.append({"call_id":call["call_id"],"gemma_equivalent":call["gemma_equivalent"],
            "same_script_sha256":old["input_sha256"]==call["input_sha256"],
            "expected":row["expected"],"qwen_raw":row["raw_predicted"],"qwen_admitted":row["predicted"],
            "gemma_raw":[b["behavior_id"] for b in oldraw["behaviors"]],
            "gemma_admitted":[b["behavior_id"] for b in old["llm"]["behaviors"]] if old.get("llm") else None,
            "qwen_seconds":row["inference_seconds"],"gemma_seconds":old["operational"]["inference_seconds"],
            "gemma_RAM_available_min_bytes":min(s["available_bytes"] for s in oldsamples),
            "gemma_tree_private_peak_bytes":max(sum(v.get("private",0) for v in s["processes"] if v.get("is_ollama_runtime")) for s in oldsamples),
            "caveat":"Same development input, single runs, different model and session. No statistical superiority claim."})
    write(OUT/"gemma_matched_comparison.json",comparisons)
    threshold=p.configuration["criteria"]["promising"]
    rows={r["call_id"]:r for r in evaluation["rows"]}
    benign_families={c["specimen"] for c in p.calls if not c["reference_labels_reviewer_only"] and rows.get(c["call_id"],{}).get("false_positives")}
    cite=evaluation["literal_citations"]
    operational=len(records)==8 and not (OUT/"execution/STOP.json").exists()
    checks={"operational_complete":operational,"usable":evaluation["usable"]>=threshold["usable_min"],
        "json":evaluation["json_valid"]>=threshold["json_min"],
        "exact":evaluation["exact_sets"]["numerator"]>=threshold["exact_min"],
        "precision":(evaluation["micro"]["precision"] or 0)>=threshold["micro_precision_min"],
        "recall":(evaluation["micro"]["recall"] or 0)>=threshold["micro_recall_min"],
        "F1":(evaluation["micro"]["F1"] or 0)>=threshold["micro_f1_min"],
        "literal_citations":bool(cite["denominator"]) and cite["numerator"]/cite["denominator"]>=threshold["literal_citation_fraction_min"],
        "both_C_usable":all(rows.get(cid,{}).get("usable",False) for cid in ("Q14-03","Q14-05")),
        "stored_executed_distinction":all(rows.get(cid,{}).get("exact",False) for cid in ("Q14-06","Q14-07")),
        "no_systematic_benign_FP":len(benign_families)<=threshold["systematic_benign_FP_max_unique_families"]}
    decision="A" if all(checks.values()) else ("B" if operational else "C")
    write(OUT/"decision_automatic.json",{"at":now(),"category":decision,"checks":checks,
        "benign_FP_unique_families":sorted(benign_families),"semantic_qualification":"Provisional until personal review; critical semantic defects can override this technical screening."})
    print(json.dumps({"decision":decision,"checks":checks,"resources":resource_summary},indent=2))


if __name__=="__main__":
    artifacts()
