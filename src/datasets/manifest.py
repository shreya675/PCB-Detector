from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from .schema import CLASS_NAMES, DatasetRecord


def write_manifest(output_root: Path, records: list[DatasetRecord]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    with (output_root / "manifest.jsonl").open("w", encoding="utf-8") as handle:
        for record in sorted(records, key=lambda item: (item.split, item.record_id)):
            handle.write(json.dumps(record.as_json(), sort_keys=True) + "\n")

    split_counts = Counter(record.split for record in records)
    class_counts = Counter(box.class_id for record in records for box in record.boxes)
    summary = {
        "images": len(records),
        "annotations": sum(class_counts.values()),
        "splits": dict(sorted(split_counts.items())),
        "classes": {CLASS_NAMES[index]: class_counts[index] for index in range(len(CLASS_NAMES))},
    }
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with (output_root / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["class_id", "class_name", "annotation_count"])
        for index, name in enumerate(CLASS_NAMES):
            writer.writerow([index, name, class_counts[index]])


def write_dataset_yaml(output_root: Path) -> None:
    names = "\n".join(f"  {index}: {name}" for index, name in enumerate(CLASS_NAMES))
    content = f"path: {output_root.resolve().as_posix()}\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n{names}\n"
    (output_root / "dataset.yaml").write_text(content, encoding="utf-8")
