from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .schema import CLASS_TO_ID, BoundingBox, canonical_class_name

# DeepPCB source IDs are 1-based and ordered differently from our canonical schema.
DEEPPCB_CLASS_ID_MAP = {1: 0, 2: 1, 3: 4, 4: 2, 5: 3, 6: 6}


def parse_deeppcb_annotation(path: Path) -> tuple[BoundingBox, ...]:
    boxes: list[BoundingBox] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = re.split(r"[\s,]+", line)
        if len(parts) != 5:
            raise ValueError(f"{path}:{line_number}: expected x1,y1,x2,y2,type")
        try:
            x1, y1, x2, y2 = map(float, parts[:4])
            source_class_id = int(parts[4])
            class_id = DEEPPCB_CLASS_ID_MAP[source_class_id]
        except (ValueError, KeyError) as exc:
            raise ValueError(f"{path}:{line_number}: invalid annotation {line!r}") from exc
        boxes.append(BoundingBox(class_id, x1, y1, x2, y2))
    return tuple(boxes)


def parse_voc_annotation(path: Path) -> tuple[str | None, tuple[BoundingBox, ...]]:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid VOC XML: {path}") from exc
    filename = root.findtext("filename")
    boxes: list[BoundingBox] = []
    for index, obj in enumerate(root.findall("object"), start=1):
        name = obj.findtext("name")
        bbox = obj.find("bndbox")
        if not name or bbox is None:
            raise ValueError(f"{path}: object {index} lacks name or bndbox")
        canonical_name = canonical_class_name(name)
        try:
            coords = [float(bbox.findtext(key, "")) for key in ("xmin", "ymin", "xmax", "ymax")]
        except ValueError as exc:
            raise ValueError(f"{path}: object {index} has invalid coordinates") from exc
        boxes.append(BoundingBox(CLASS_TO_ID[canonical_name], *coords))
    return filename, tuple(boxes)


def write_yolo_label(path: Path, boxes: tuple[BoundingBox, ...], width: int, height: int) -> None:
    lines = [box.to_yolo(width, height) for box in boxes]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
