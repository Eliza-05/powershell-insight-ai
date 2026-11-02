"""Read-only text similarity audit; never a proof of semantic independence."""

from __future__ import annotations

import base64
import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def canonical(text: str) -> str:
    text = re.sub(r"(?m)^\s*(?:#.*|<\#.*\#>)$", "", text)
    text = re.sub(r"'(?:''|[^'])*'|\"(?:`.|[^\"])*\"", " <string> ", text)
    text = re.sub(r"\$[\w:]+", " $variable ", text)
    text = re.sub(r"\b\d+\b", " <number> ", text)
    return " ".join(text.casefold().split())


def decoded_if_launcher(text: str) -> str:
    match = re.search(r"(?i)-EncodedCommand\s+([A-Za-z0-9+/=]+)", text)
    return base64.b64decode(match.group(1), validate=True).decode("utf-16le") if match else text


def audit() -> dict:
    manifest = json.loads((ROOT / "datasets/metadata/pilot_v2_manifest.json").read_text(encoding="utf-8"))
    rows = manifest["cases"]
    normalized = {row["case_id"]: canonical(decoded_if_launcher((ROOT / row["file_ref"]).read_text(encoding="utf-8")))
                  for row in rows}
    comparisons = []
    for dev in (r for r in rows if r["split"] == "development"):
        for selection in (r for r in rows if r["split"] == "selection"):
            left, right = normalized[dev["case_id"]], normalized[selection["case_id"]]
            comparisons.append({"development": dev["case_id"], "selection": selection["case_id"],
                                "same_canonical_text": left == right,
                                "similarity": round(difflib.SequenceMatcher(None, left, right, autojunk=False).ratio(), 4)})
    historical = []
    history_paths = sorted((ROOT / "datasets/safe_samples/pilot").glob("PILOT-P*.ps1.txt"))
    history_paths += sorted((ROOT / "backend/tests/deobfuscation/fixtures").glob("*.ps1.txt"))
    for path in history_paths:
        old = canonical(decoded_if_launcher(path.read_text(encoding="utf-8")))
        for row in rows:
            new = normalized[row["case_id"]]
            historical.append({"old_file": path.relative_to(ROOT).as_posix(), "new_case": row["case_id"],
                               "same_canonical_text": old == new,
                               "similarity": round(difflib.SequenceMatcher(None, old, new, autojunk=False).ratio(), 4)})
    return {"status": "preliminary_text_audit_human_family_review_pending", "threshold_for_review_flag": 0.72,
            "method": "casefold/whitespace/literal-variable-number abstraction and SequenceMatcher; not PowerShell parsing",
            "limitations": ["Author constructed both splits; not blind reserve authorship.",
                           "Taxonomy primitives necessarily overlap; similarity is not leakage by itself.",
                           "No semantic clone proof; detector fixtures embedded in Python need contextual human review."],
            "source_bindings": {r["case_id"]: r["sha256"] for r in rows},
            "cross_split_comparisons": len(comparisons),
            "cross_split_canonical_duplicates": [r for r in comparisons if r["same_canonical_text"]],
            "cross_split_review_flags": [r for r in comparisons if r["similarity"] >= 0.72],
            "highest_cross_split_pairs": sorted(comparisons, key=lambda r: -r["similarity"])[:10],
            "historical_comparisons": len(historical),
            "historical_canonical_duplicates": [r for r in historical if r["same_canonical_text"]],
            "historical_review_flags": [r for r in historical if r["similarity"] >= 0.72],
            "audit_input_sha256": hashlib.sha256(json.dumps(normalized, sort_keys=True).encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
