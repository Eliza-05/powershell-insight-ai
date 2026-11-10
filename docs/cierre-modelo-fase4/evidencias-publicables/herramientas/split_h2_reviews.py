"""Split the single H2 download into one file per output, without changing any reviewed value.

Usage: python split_h2_reviews.py <revision_H2_Karol.json> <out_dir>
Writes <out_dir>/<unit>-<mode>.json (exclusive create) and a manifest with hashes.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def main(source, out_dir):
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    manifest = {"source": str(Path(source).resolve()), "source_sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                "reviewer": data["reviewer"], "files": {}}
    for key, review in sorted(data["reviews"].items()):
        path = out / (key + ".json")
        with path.open("x", encoding="utf-8") as h:
            json.dump(review, h, ensure_ascii=False, indent=2)
            h.write("\n")
        manifest["files"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out / "SPLIT_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(manifest["files"]), "revisiones")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
