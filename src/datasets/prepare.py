from __future__ import annotations

import json
import shutil
from pathlib import Path

from .converters import parse_deeppcb_annotation, parse_voc_annotation, write_yolo_label
from .io import IMAGE_SUFFIXES, read_image_size, sha256_file
from .manifest import write_dataset_yaml, write_manifest
from .schema import DatasetRecord
from .splitting import assert_no_group_leakage, board_group, stable_split


def _copy_record(source_image: Path, source_label: Path, output: Path, split: str, record_id: str,
                 boxes, reference: Path | None, dataset_name: str) -> DatasetRecord:
    width, height = read_image_size(source_image)
    errors = [error for box in boxes for error in box.validate(width, height)]
    if errors:
        raise ValueError(f"{source_label}: " + "; ".join(errors))
    image_suffix = source_image.suffix.lower()
    image_out = output / "images" / split / f"{record_id}{image_suffix}"
    label_out = output / "labels" / split / f"{record_id}.txt"
    image_out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image, image_out)
    write_yolo_label(label_out, boxes, width, height)
    reference_out: Path | None = None
    if reference:
        read_image_size(reference)
        reference_out = output / "references" / split / f"{record_id}{reference.suffix.lower()}"
        reference_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(reference, reference_out)
    return DatasetRecord(
        record_id=record_id, split=split, image=image_out.relative_to(output).as_posix(),
        label=label_out.relative_to(output).as_posix(), width=width, height=height,
        boxes=boxes, source_dataset=dataset_name,
        reference_image=reference_out.relative_to(output).as_posix() if reference_out else None,
        source_image=str(source_image.resolve()), source_annotation=str(source_label.resolve()),
        sha256=sha256_file(image_out),
    )


def _record_id_from_list_entry(entry: str) -> str:
    """'group20085/20085/20085000.jpg group20085/20085_not/20085000.txt' -> '20085000'."""
    image_part = entry.split()[0]
    stem = Path(image_part).stem
    return stem.removesuffix("_test").removesuffix("_temp")


def load_official_split(list_dir: Path) -> dict[str, str]:
    """Read DeepPCB's official trainval.txt / test.txt and map record_id -> 'trainval' | 'test'."""
    mapping: dict[str, str] = {}
    for name, split in (("trainval.txt", "trainval"), ("test.txt", "test")):
        path = list_dir / name
        if not path.is_file():
            raise ValueError(f"Official split list not found: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record_id = _record_id_from_list_entry(line)
                if mapping.get(record_id, split) != split:
                    raise ValueError(f"Record {record_id} appears in both trainval and test lists")
                mapping[record_id] = split
    return mapping


def prepare_deeppcb(source: Path, output: Path, val_fraction: float = 0.1,
                    official_split_dir: Path | None = None) -> list[DatasetRecord]:
    """Convert DeepPCB.

    Default: deterministic grouped split (whole board groups stay together; ``val_fraction``
    widens the validation bucket, the test bucket is unchanged).
    With ``official_split_dir``: use the upstream trainval.txt / test.txt lists (the paper's
    1000/500 benchmark protocol, boards shared between splits) and carve ``val_fraction`` of
    the trainval images out for validation, deterministically by record id.
    """
    official = load_official_split(official_split_dir) if official_split_dir else None
    candidates = sorted(path for path in source.rglob("*_test.*") if path.suffix.lower() in IMAGE_SUFFIXES)
    if not candidates:
        raise ValueError(f"No DeepPCB *_test images found below {source}")
    records: list[DatasetRecord] = []
    groups: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for image in candidates:
        record_id = image.stem.removesuffix("_test")
        if record_id in seen_ids:
            raise ValueError(f"Duplicate DeepPCB record ID: {record_id}")
        seen_ids.add(record_id)
        annotation = image.with_name(f"{record_id}.txt")
        if not annotation.is_file():
            # Official distribution keeps labels in a sibling <board>_not folder.
            annotation = image.parent.parent / f"{image.parent.name}_not" / f"{record_id}.txt"
        reference = image.with_name(f"{record_id}_temp{image.suffix}")
        if not annotation.is_file() or not reference.is_file():
            raise ValueError(f"Incomplete DeepPCB pair for {image}: label={annotation.exists()}, reference={reference.exists()}")
        group = next((p.name for p in image.parents if p.name.startswith("group")), board_group(record_id))
        if official is not None:
            if record_id not in official:
                raise ValueError(f"{record_id} is not listed in the official trainval/test lists")
            if official[record_id] == "test":
                split = "test"
            else:
                split = "val" if stable_split(record_id, train=1 - val_fraction, val=0.0) != "train" else "train"
        else:
            split = stable_split(group, train=0.9 - val_fraction, val=val_fraction)
        groups.append((group, split))
        records.append(_copy_record(image, annotation, output, split, record_id,
                                    parse_deeppcb_annotation(annotation), reference, "DeepPCB"))
    if official is None:
        assert_no_group_leakage(groups)
    write_manifest(output, records)
    write_dataset_yaml(output)
    return records


def prepare_hripcb(source: Path, output: Path) -> list[DatasetRecord]:
    annotations = sorted(source.rglob("*.xml"))
    if not annotations:
        raise ValueError(f"No Pascal VOC XML annotations found below {source}")
    images = {}
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
            if path.name in images:
                raise ValueError(f"Ambiguous HRIPCB image filename: {path.name}")
            images[path.name] = path
    records: list[DatasetRecord] = []
    groups: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    for annotation in annotations:
        filename, boxes = parse_voc_annotation(annotation)
        image = images.get(filename or "")
        if image is None:
            matching = [path for name, path in images.items() if Path(name).stem == annotation.stem]
            if len(matching) != 1:
                raise ValueError(f"Cannot resolve image for {annotation}")
            image = matching[0]
        record_id = image.stem
        if record_id in seen_ids:
            raise ValueError(f"Duplicate HRIPCB record ID: {record_id}")
        seen_ids.add(record_id)
        group = board_group(record_id)
        split = stable_split(group)
        groups.append((group, split))
        records.append(_copy_record(image, annotation, output, split, record_id, boxes, None, "HRIPCB"))
    assert_no_group_leakage(groups)
    write_manifest(output, records)
    write_dataset_yaml(output)
    return records


def validate_prepared_dataset(root: Path) -> dict[str, int]:
    manifest = root / "manifest.jsonl"
    if not manifest.is_file():
        raise ValueError(f"Missing manifest: {manifest}")
    image_count = annotation_count = 0
    seen_ids: set[str] = set()
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        item = json.loads(line)
        if item["record_id"] in seen_ids:
            raise ValueError(f"Duplicate record_id at manifest line {line_number}")
        seen_ids.add(item["record_id"])
        image_path, label_path = root / item["image"], root / item["label"]
        width, height = read_image_size(image_path)
        if (width, height) != (item["width"], item["height"]):
            raise ValueError(f"Dimension mismatch for {image_path}")
        if not label_path.is_file():
            raise ValueError(f"Missing label: {label_path}")
        image_count += 1
        annotation_count += len(item["boxes"])
    return {"images": image_count, "annotations": annotation_count}
