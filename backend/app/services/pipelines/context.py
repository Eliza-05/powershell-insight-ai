"""Common policy and strictly allowlisted 1A context. No dependency on 1B."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.schemas.deobfuscation import DeobfuscationResult

PROMPT_VERSION = "application-analysis-v1"
POLICY_PATH = Path(__file__).with_name("policy_v1.md")


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AnalysisContext:
    messages: list[dict[str, str]]
    sources: dict[str, str]
    deobfuscation: DeobfuscationResult | None
    prompt_sha256: str
    context_sha256: str


def build_context(script: str, deobfuscation: DeobfuscationResult | None = None, *,
                  policy_path: Path = POLICY_PATH, preprocess=None) -> AnalysisContext:
    """`preprocess` (optional) rewrites only the text shown to the model, never `sources`.

    It must preserve length and offsets (e.g. comment blanking) so citations stay literal in
    the real original/recovery, which is what validation checks. Defaults keep v1 unchanged.
    """
    policy = Path(policy_path).read_text(encoding="utf-8")
    show = preprocess or (lambda text: text)
    sources = {"original": script}
    data = {"original": show(script)}
    if deobfuscation is not None:
        # Revalidate nested/mutable structures before trusting trace provenance.
        deobfuscation = DeobfuscationResult.model_validate(deobfuscation.model_dump())
        if deobfuscation.input_sha256 != sha(script):
            raise ValueError("Deobfuscation belongs to another input")
        traces = []
        for t in deobfuscation.transformations:
            if t.deterministic_verified and t.recovered_text is not None and t.status == "success":
                sources[t.transformation_id] = t.recovered_text
                traces.append({"source_id": t.transformation_id, "text": show(t.recovered_text),
                               "technique": t.technique.value, "recovery_kind": t.recovery_kind,
                               "source": t.source.model_dump(), "root_source": t.root_source.model_dump(),
                               "original_fragment": show(t.original_fragment), "dependencies": t.dependencies,
                               "warnings": t.warnings})
        data["deterministic_recovery"] = {"verified_texts": traces,
            "unresolved": [u.model_dump(mode="json") for u in deobfuscation.unresolved],
            "limits_hit": deobfuscation.limits_hit, "warnings": deobfuscation.warnings,
            "semantic_equivalence": "not_claimed"}
    # JSON encoding is data framing, not an invitation to obey embedded instructions.
    content = canonical(data)
    return AnalysisContext(messages=[{"role": "system", "content": policy}, {"role": "user", "content": content}],
                           sources=sources, deobfuscation=deobfuscation,
                           prompt_sha256=sha(policy), context_sha256=sha(content))
