"""Repository-only overlap audit, not proof of absence from model pretraining."""
from __future__ import annotations

import ast
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re

from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation.budget import Budget
from app.services.deobfuscation.engine import deobfuscate
from app.services.deobfuscation.lexer import lex
from experiments.phase4.common import ROOT, OUT

SIGNAL = re.compile(r"(?i)(\$\w|[a-z]+-[a-z]+|\[\w+(?:\.\w+)+\]|encodedcommand)")


def normalized_tokens(text):
    tokens, _ = lex(text, Budget(DeobfuscationLimits()))
    result = []
    for token in tokens:
        if token.kind == "COMMENT": continue
        if token.kind == "STRING": result.append("STRING")
        elif token.kind == "VAR": result.append("VAR")
        elif token.kind == "WORD" and (token.value or "").isdigit(): result.append("NUMBER")
        elif token.kind == "NL": result.append("SEP")
        else: result.append(token.kind + ":" + (token.value or "").casefold())
    return result


def views(text):
    # Decoded views prevent disguising an old base with a different wrapper.
    result = [text]
    try:
        recovered = deobfuscate(text)
        result.extend(t.recovered_text for t in recovered.transformations
                      if t.deterministic_verified and t.recovered_text and len(t.recovered_text) >= 20
                      and SIGNAL.search(t.recovered_text))
    except (ValueError, RuntimeError):
        pass
    return list(dict.fromkeys(result))


def corpus(root=ROOT):
    candidates = {}
    baseline = root / "artifacts/phase4_preparation/protected_before.json"
    prior_names = set(json.loads(baseline.read_text(encoding="utf-8"))) if baseline.exists() else None
    def add(text, origin):
        if isinstance(text, str) and 20 <= len(text) <= 65536 and SIGNAL.search(text):
            key = hashlib.sha256(text.encode("utf-8")).hexdigest()
            candidates.setdefault(key, {"text": text, "origins": []})["origins"].append(origin)
    def walk_json(value, origin):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"original", "script", "script_text", "source_text", "powershell"}: add(child, origin + ":" + key)
                if isinstance(child, (dict, list)): walk_json(child, origin)
        elif isinstance(value, list):
            for child in value: walk_json(child, origin)
    bases = [root / "datasets/safe_samples", root / "datasets/metadata", root / "experiments", root / "artifacts", root / "backend/tests"]
    for base in bases:
        for path in base.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts or path.is_relative_to(OUT): continue
            if "diagnostic_source_archive" in path.parts: continue
            relative = path.relative_to(root).as_posix()
            if prior_names is not None and relative not in prior_names: continue
            if path.name.endswith((".ps1", ".ps1.txt")):
                add(path.read_text(encoding="utf-8-sig", errors="replace"), relative)
            elif path.suffix == ".json":
                try: walk_json(json.loads(path.read_text(encoding="utf-8-sig")), relative)
                except (ValueError, UnicodeError): pass
            elif path.suffix == ".py" and not path.is_relative_to(root / "experiments/phase4"):
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Constant): add(node.value, relative + ":literal")
                except (ValueError, SyntaxError, UnicodeError): pass
    return candidates


def audit(cases, root=ROOT):
    old = corpus(root)
    prior = []
    seen_views = set()
    for item in old.values():
        for view in views(item["text"]):
            tokens = normalized_tokens(view)
            signature = tuple(tokens)
            if len(tokens) < 3 or signature in seen_views: continue
            seen_views.add(signature)
            prior.append((tokens, item["origins"][0]))
    rows = []
    for case in cases:
        new_views = [normalized_tokens(v) for v in views(case["script"])]
        original = new_views[0]
        nearest = sorted(((SequenceMatcher(None, original, tokens, autojunk=False).ratio(), origin)
                          for tokens, origin in prior), reverse=True)[:3]
        # Substring coincidences of short primitive commands are disclosed; only
        # equality of full program structure is an automatic duplicate blocker.
        equivalents = [origin for tokens, origin in prior
                       if any(tokens == view for view in new_views if len(view) >= 3)]
        rows.append({"id": case["id"], "exact_duplicate": hashlib.sha256(case["script"].encode()).hexdigest() in old,
            "normalized_program_equivalents": equivalents, "nearest_prior_programs": [{"token_similarity": score, "origin": origin} for score, origin in nearest],
            "decoded_view_count": len(new_views), "novel_logic_author_rationale": case["novel_logic"],
            "human_semantic_independence_review": "pending_required_before_freeze"})
    internal = []
    for i, a in enumerate(cases):
        for b in cases[i + 1:]:
            score = SequenceMatcher(None, normalized_tokens(a["script"]), normalized_tokens(b["script"]), autojunk=False).ratio()
            if score >= .55:
                internal.append({"a": a["id"], "b": b["id"], "token_similarity": score,
                    "same_cluster": a["cluster"] == b["cluster"], "review": "Check dataflow/invocation, not just identifier differences"})
    return {"prior_unique_exact_texts": len(old), "prior_unique_normalized_views": len(prior),
        "scope": "Local synthetic datasets, prior campaign inputs embedded in JSON, and development/test literals. No raw/external/private/quarantine samples read.",
        "algorithm": "Comments ignored; variable names, string literals and numeric values normalized; full programs and deterministic decoded views compared. Top token similarities plus authored semantic rationales require personal review.",
        "cases": rows, "internal_similarity_flags": internal,
        "automatic_exact_or_program_duplicate_found": any(r["exact_duplicate"] or r["normalized_program_equivalents"] for r in rows),
        "limitations": ["Structural similarity is a screening aid, not semantic equivalence proof.",
            "Shared taxonomy primitives are unavoidable; different command names alone do not establish new logic.",
            "Generated by the same assistant with historical exposure; independence from model pretraining cannot be proven.",
            "Owner must adjudicate semantic novelty and cluster grouping before freezing."]}
