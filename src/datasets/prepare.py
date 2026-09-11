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


def prepare_deeppcb(source: Path, output: Path) -> list[DatasetRecord]:
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
        split = stable_split(group)
        groups.append((group, split))
        records.append(_copy_record(image, annotation, output, split, record_id,
                                    parse_deeppcb_annotation(annotation), reference, "DeepPCB"))
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
