from __future__ import annotations

from pathlib import Path
from threading import Lock

import numpy as np

from src.ml.classes import resolve_model_classes
from src.ml.metadata import sha256_file

from .contracts import DefectFinding


class ModelUnavailableError(RuntimeError):
    pass


class UltralyticsDefectDetector:
    def __init__(self, weights: Path, confidence: float = 0.25, model_factory=None):
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        self.weights = weights
        self.confidence = confidence
        self._factory = model_factory
        self._model = None
        self._version = None
        self._names = None
        self._lock = Lock()

    @property
    def model_version(self) -> str:
        if self._version is None:
            if not self.weights.is_file():
                return "unavailable"
            self._version = f"sha256:{sha256_file(self.weights)[:12]}"
        return self._version

    def _load(self):
        if not self.weights.is_file():
            raise ModelUnavailableError(f"Model weights are unavailable: {self.weights}")
        if self._model is not None:
            return self._model
        factory = self._factory
        if factory is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise ModelUnavailableError("Ultralytics is not installed. Install the ML dependencies.") from exc
            factory = YOLO
        try:
            model = factory(str(self.weights))
            if getattr(model, "task", "detect") != "detect":
                raise ValueError("Checkpoint must be an object detection model")
            self._names = resolve_model_classes(model.names)
        except Exception as exc:
            raise ModelUnavailableError("Cannot load a compatible PCB checkpoint; check weights and class names.") from exc
        self._model = model
        return self._model

    def detect(self, image: np.ndarray) -> tuple[DefectFinding, ...]:
        # Ultralytics keeps mutable predictor state on the shared model instance.
        with self._lock:
            return self._detect(image)

    def _detect(self, image: np.ndarray) -> tuple[DefectFinding, ...]:
        results = self._load().predict(source=image, conf=self.confidence, save=False, verbose=False)
        if not results:
            return ()
        result = results[0]
        boxes = result.boxes
        if boxes is None:
            raise ModelUnavailableError("Checkpoint did not return detection boxes")
        findings = []
        for coords, score, class_value in zip(
            boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist(), strict=True,
        ):
            class_id = int(class_value)
            if class_value != class_id or class_id not in self._names:
                raise ModelUnavailableError(f"Model returned unsupported class ID: {class_id}")
            if (len(coords) != 4 or not np.isfinite(coords).all() or not np.isfinite(score)
                    or not 0 <= score <= 1 or coords[2] <= coords[0] or coords[3] <= coords[1]):
                raise ModelUnavailableError("Model returned invalid detection coordinates or confidence")
            findings.append(DefectFinding(self._names[class_id], tuple(map(float, coords)),
                                          float(score), "yolo_defect"))
        return tuple(findings)
