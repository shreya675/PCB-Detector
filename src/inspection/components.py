from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class BoundingBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def validate(self) -> None:
        if self.x_min < 0 or self.y_min < 0 or self.x_max <= self.x_min or self.y_max <= self.y_min:
            raise ValueError(f"Invalid component bounding box: {self}")

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x_min + self.x_max) / 2, (self.y_min + self.y_max) / 2)


@dataclass(frozen=True)
class ComponentDetection:
    detection_id: str
    label: str
    box: BoundingBox
    orientation_degrees: float = 0.0
    mean_intensity: float | None = None
    confidence: float | None = None
    source: str = "unknown"

    def validate(self) -> None:
        self.box.validate()
        if not self.detection_id or not self.label:
            raise ValueError("Component ID and label cannot be empty")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("Component confidence must be between 0 and 1")


class ComponentDetector(Protocol):
    def detect(self, image: np.ndarray) -> tuple[ComponentDetection, ...]: ...
