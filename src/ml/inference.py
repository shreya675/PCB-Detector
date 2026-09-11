from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.datasets.schema import CLASS_NAMES

from .classes import resolve_model_classes


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float


@dataclass(frozen=True)
class Prediction:
    source: str
    annotated_image: str | None
    detections: tuple[Detection, ...]


def _default_model_factory(weights: str):
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError("Ultralytics is not installed. Run: pip install -e '.[ml]'") from exc
    return YOLO(weights)


def parse_result(result: Any, annotated_image: Path | None = None) -> Prediction:
    detections: list[Detection] = []
    names = resolve_model_classes(getattr(result, "names", None))
    boxes = getattr(result, "boxes", None)
    if boxes is not None:
        xyxy = boxes.xyxy.cpu().tolist()
        confidence = boxes.conf.cpu().tolist()
        classes = boxes.cls.cpu().tolist()
        for coords, score, class_value in zip(xyxy, confidence, classes, strict=True):
            class_id = int(class_value)
            if class_value != class_id or class_id not in names:
                raise ValueError(f"Model returned unsupported class ID: {class_id}")
            name = names[class_id]
            detections.append(Detection(CLASS_NAMES.index(name), name, float(score), *map(float, coords)))
    source = str(getattr(result, "path", ""))
    return Prediction(source, str(annotated_image) if annotated_image else None, tuple(detections))


def predict_images(weights: Path, sources: list[Path], output: Path, confidence: float = 0.25,
                   iou: float = 0.50, image_size: int = 640, device: str = "auto",
                   model_factory=None) -> list[Prediction]:
    if not weights.is_file():
        raise ValueError(f"Weights not found: {weights}")
    if not sources or any(not source.is_file() for source in sources):
        raise ValueError("Every inference source must be an existing file")
    output.mkdir(parents=True, exist_ok=True)
    factory = model_factory or _default_model_factory
    model = factory(str(weights))
    results = model.predict(source=[str(path) for path in sources], conf=confidence, iou=iou,
                            imgsz=image_size, device="" if device == "auto" else device,
                            save=False, verbose=False)
    predictions: list[Prediction] = []
    for index, result in enumerate(results):
        annotated = output / f"{Path(str(getattr(result, 'path', sources[index]))).stem}_annotated.jpg"
        result.save(filename=str(annotated))
        predictions.append(parse_result(result, annotated))
    payload = [{**asdict(item), "detections": [asdict(det) for det in item.detections]} for item in predictions]
    (output / "predictions.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return predictions
