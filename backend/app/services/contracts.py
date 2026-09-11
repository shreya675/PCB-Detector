from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class DefectFinding:
    defect_type: str
    bbox: tuple[float, float, float, float]
    confidence: float | None
    source: str
    severity: str | None = None
    metadata: dict | None = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class InspectionOutcome:
    status: str
    findings: tuple[DefectFinding, ...]
    severity_counts: dict[str, int]
    annotated_image: np.ndarray
    alignment_quality: dict | None
    summary: dict


class DefectDetector(Protocol):
    @property
    def model_version(self) -> str: ...
    def detect(self, image: np.ndarray) -> tuple[DefectFinding, ...]: ...
