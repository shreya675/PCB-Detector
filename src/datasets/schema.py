from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CLASS_NAMES = (
    "open_circuit",
    "short_circuit",
    "spur",
    "spurious_copper",
    "mouse_bite",
    "missing_hole",
    "pin_hole",
)
CLASS_TO_ID = {name: index for index, name in enumerate(CLASS_NAMES)}

ALIASES = {
    "open": "open_circuit", "open_circuit": "open_circuit", "open-circuit": "open_circuit",
    "short": "short_circuit", "short_circuit": "short_circuit", "short-circuit": "short_circuit",
    "spur": "spur", "copper": "spurious_copper", "spurious_copper": "spurious_copper",
    "spurious-copper": "spurious_copper", "mousebite": "mouse_bite", "mouse_bite": "mouse_bite",
    "mouse-bite": "mouse_bite", "pinhole": "pin_hole", "pin_hole": "pin_hole",
    "pin-hole": "pin_hole", "missing_hole": "missing_hole", "missing-hole": "missing_hole",
}


@dataclass(frozen=True)
class BoundingBox:
    class_id: int
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def validate(self, width: int, height: int) -> list[str]:
        errors: list[str] = []
        if self.class_id not in range(len(CLASS_NAMES)):
            errors.append(f"unknown class_id={self.class_id}")
        if not (0 <= self.x_min < self.x_max <= width):
            errors.append(f"invalid x coordinates: {self.x_min}, {self.x_max}, width={width}")
        if not (0 <= self.y_min < self.y_max <= height):
            errors.append(f"invalid y coordinates: {self.y_min}, {self.y_max}, height={height}")
        return errors

    def to_yolo(self, width: int, height: int) -> str:
        errors = self.validate(width, height)
        if errors:
            raise ValueError("; ".join(errors))
        x_center = ((self.x_min + self.x_max) / 2) / width
        y_center = ((self.y_min + self.y_max) / 2) / height
        box_width = (self.x_max - self.x_min) / width
        box_height = (self.y_max - self.y_min) / height
        return f"{self.class_id} {x_center:.8f} {y_center:.8f} {box_width:.8f} {box_height:.8f}"


@dataclass(frozen=True)
class DatasetRecord:
    record_id: str
    split: str
    image: str
    label: str
    width: int
    height: int
    boxes: tuple[BoundingBox, ...]
    source_dataset: str
    reference_image: str | None = None
    source_image: str | None = None
    source_annotation: str | None = None
    sha256: str | None = None

    def as_json(self) -> dict[str, Any]:
        result = asdict(self)
        result["boxes"] = [asdict(box) for box in self.boxes]
        return result


def canonical_class_name(value: str) -> str:
    key = value.strip().lower().replace(" ", "_")
    if key not in ALIASES:
        raise ValueError(f"Unsupported PCB defect class: {value!r}")
    return ALIASES[key]


def ensure_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()
