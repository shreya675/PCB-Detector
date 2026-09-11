from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

from src.datasets.io import IMAGE_SUFFIXES
from src.datasets.schema import CLASS_NAMES


@dataclass(frozen=True)
class DatasetPreflight:
    dataset_yaml: Path
    root: Path
    split_counts: dict[str, int]
    class_names: tuple[str, ...]

    @property
    def total_images(self) -> int:
        return sum(self.split_counts.values())


def _resolve_names(raw_names) -> tuple[str, ...]:
    if isinstance(raw_names, dict):
        if {int(key) for key in raw_names} != set(range(len(raw_names))):
            raise ValueError("Dataset class IDs must be contiguous from zero")
        ordered = [raw_names[key] for key in sorted(raw_names, key=lambda item: int(item))]
    elif isinstance(raw_names, list):
        ordered = raw_names
    else:
        raise ValueError("Dataset YAML must define names as a list or integer-keyed mapping")  # noqa: TRY004 - invalid configuration file value
    return tuple(str(name) for name in ordered)


def validate_yolo_dataset(dataset_yaml: Path, require_test: bool = False) -> DatasetPreflight:
    if not dataset_yaml.is_file():
        raise ValueError(f"Dataset YAML not found: {dataset_yaml}")
    raw = yaml.safe_load(dataset_yaml.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Dataset YAML must contain a mapping")  # noqa: TRY004 - invalid configuration file value
    yaml_root = Path(raw.get("path", "."))
    root = yaml_root if yaml_root.is_absolute() else (dataset_yaml.parent / yaml_root).resolve()
    names = _resolve_names(raw.get("names"))
    if names != CLASS_NAMES:
        raise ValueError(f"Class order mismatch. Expected {CLASS_NAMES}, got {names}")
    required = ["train", "val"] + (["test"] if require_test else [])
    counts: dict[str, int] = {}
    for split in required:
        relative = raw.get(split)
        if not relative:
            raise ValueError(f"Dataset YAML is missing the {split!r} split")
        image_dir = root / relative
        if not image_dir.is_dir():
            raise ValueError(f"Image directory not found for {split}: {image_dir}")
        images = sorted(path for path in image_dir.rglob("*") if path.suffix.lower() in IMAGE_SUFFIXES)
        if not images:
            raise ValueError(f"No images found in {split}: {image_dir}")
        labels_dir = root / "labels" / split
        missing = [image.name for image in images if not (labels_dir / f"{image.stem}.txt").is_file()]
        if missing:
            raise ValueError(f"Missing {len(missing)} labels in {split}; first: {missing[0]}")
        for image in images:
            label = labels_dir / f"{image.stem}.txt"
            for number, line in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                values = line.split()
                try:
                    if len(values) != 5:
                        raise ValueError("expected class and four coordinates")
                    class_id = int(values[0])
                    x, y, width, height = map(float, values[1:])
                    if class_id not in range(len(names)) or not all(math.isfinite(v) for v in (x, y, width, height)):
                        raise ValueError("invalid class or non-finite coordinates")
                    tolerance = 1e-7
                    if not (0 < width <= 1 and 0 < height <= 1 and
                            width / 2 - tolerance <= x <= 1 - width / 2 + tolerance and
                            height / 2 - tolerance <= y <= 1 - height / 2 + tolerance):
                        raise ValueError("box extends outside the normalized image")
                except ValueError as exc:
                    raise ValueError(f"{label}:{number}: invalid YOLO annotation: {exc}") from exc
        counts[split] = len(images)
    return DatasetPreflight(dataset_yaml.resolve(), root, counts, names)
