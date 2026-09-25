"""Archive local checkpoints and matching evaluation evidence without overwriting files.

Run from any directory: python scripts/snapshot_baselines.py --name baseline-v1
This verifies artifact identity, not the correctness or independence of evaluations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", args.name):
        parser.error("Use a lowercase name starting with a letter, then letters/digits/hyphens.")
    root = Path(__file__).resolve().parents[1]
    weights = sorted((root / "models/weights").glob("*.pt"))
    if not weights:
        raise SystemExit("No checkpoints found.")
    backup = root / "models/weights/baselines" / args.name
    evidence = root / "docs/baselines" / args.name
    if backup.exists() or evidence.exists():
        raise SystemExit("Snapshot already exists; choose a new name. Nothing overwritten.")
    evaluations = []
    for folder in (root / "runs", root / "reports"):
        for path in sorted(folder.rglob("metrics.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("mode") == "evaluation":
                evaluations.append((path, record))
    backup.mkdir(parents=True)
    evidence.mkdir(parents=True)

    def copy_verified(source: Path, destination: Path) -> str:
        original_hash = sha256(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as src, destination.open("xb") as dst:
            shutil.copyfileobj(src, dst)
        if sha256(destination) != original_hash:
            raise RuntimeError(f"Copy verification failed: {destination}")
        return original_hash

    records = []
    for weight in weights:
        destination = backup / weight.name
        fingerprint = copy_verified(weight, destination)
        matches = []
        for path, result in evaluations:
            if result.get("weights", {}).get("sha256", "").lower() != fingerprint:
                continue
            archived = evidence / "evaluations" / path.relative_to(root)
            report_hash = copy_verified(path, archived)
            matches.append({
                "source": path.relative_to(root).as_posix(),
                "archived_report": archived.relative_to(root).as_posix(),
                "report_sha256": report_hash,
                "dataset": result.get("dataset"),
                "config": result.get("config"),
                "metrics": result.get("metrics"),
            })
        records.append({"source": weight.relative_to(root).as_posix(),
                        "backup": destination.relative_to(root).as_posix(),
                        "bytes": weight.stat().st_size, "sha256": fingerprint,
                        "evaluations": matches})
    dataset_records = []
    for folder in sorted((root / "data/processed").iterdir()):
        if not folder.is_dir():
            continue
        for name in ("dataset.yaml", "manifest.jsonl", "summary.json"):
            source = folder / name
            if source.is_file():
                destination = backup / "dataset-metadata" / folder.name / name
                fingerprint = copy_verified(source, destination)
                dataset_records.append({"source": source.relative_to(root).as_posix(),
                                        "backup": destination.relative_to(root).as_posix(),
                                        "sha256": fingerprint})
    manifest = {"created_at": datetime.now(UTC).isoformat(),
                "scope": "Local artifact snapshot; no new training or evaluation performed.",
                "limitations": ["Dataset metadata is copied; image files are not backed up.",
                                "Checkpoint/report hash matches do not establish test independence.",
                                "Repeated test-set experiments must not be called untouched evaluation."],
                "checkpoints": records, "dataset_metadata": dataset_records}
    output = evidence / "manifest.json"
    with output.open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(f"Verified {len(records)} checkpoint backups, "
          f"{sum(len(r['evaluations']) for r in records)} matching reports, "
          f"{len(dataset_records)} dataset metadata files.")
    print(f"Manifest: {output}")


if __name__ == "__main__":
    main()
