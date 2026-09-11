from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class YoloExperimentConfig:
    model: str = "yolo11n.pt"
    data: str = "data/processed/deeppcb/dataset.yaml"
    epochs: int = 100
    image_size: int = 640
    batch: int = 16
    workers: int = 4
    device: str = "auto"
    seed: int = 42
    deterministic: bool = True
    patience: int = 25
    confidence: float = 0.25
    iou: float = 0.50
    project: str = "reports/training"
    name: str = "deeppcb-yolo11n-baseline"
    evaluation_split: str = "test"

    def validate(self) -> None:
        if self.evaluation_split not in {"val", "test"}:
            raise ValueError("evaluation_split must be val or test")
        if self.epochs < 1 or self.image_size < 32 or self.batch < 1 or self.workers < 0:
            raise ValueError("epochs, image_size, and batch must be positive; workers cannot be negative")
        if not 0 <= self.confidence <= 1 or not 0 <= self.iou <= 1:
            raise ValueError("confidence and iou thresholds must be between 0 and 1")
        if not self.name.strip() or not self.project.strip():
            raise ValueError("project and name cannot be empty")

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_experiment_config(path: Path) -> YoloExperimentConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping in {path}")  # noqa: TRY004 - invalid configuration file value
    unknown = set(raw) - set(YoloExperimentConfig.__dataclass_fields__)
    if unknown:
        raise ValueError(f"Unknown experiment settings: {sorted(unknown)}")
    config = YoloExperimentConfig(**raw)
    config.validate()
    return config
