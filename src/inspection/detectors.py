from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from src.cv.preprocessing import to_grayscale, validate_image

from .components import BoundingBox, ComponentDetection


@dataclass(frozen=True)
class ContourDetectorConfig:
    minimum_area: int = 80
    maximum_area_ratio: float = 0.08
    minimum_aspect_ratio: float = 0.15
    maximum_aspect_ratio: float = 6.5
    morphology_kernel: int = 3
    border_margin: int = 3

    def validate(self) -> None:
        if self.minimum_area < 1 or not 0 < self.maximum_area_ratio <= 1:
            raise ValueError("Area thresholds are invalid")
        if self.minimum_aspect_ratio <= 0 or self.maximum_aspect_ratio < self.minimum_aspect_ratio:
            raise ValueError("Aspect-ratio thresholds are invalid")
        if self.morphology_kernel < 1 or self.border_margin < 0:
            raise ValueError("Morphology kernel and border margin are invalid")


class ContourComponentDetector:
    """Dataset-free baseline that proposes dark, component-like connected regions.

    Its outputs are geometric candidates, not learned component classifications.
    """

    def __init__(self, config: ContourDetectorConfig | None = None):
        self.config = config or ContourDetectorConfig()
        self.config.validate()

    def detect(self, image: np.ndarray) -> tuple[ComponentDetection, ...]:
        validate_image(image)
        gray = to_grayscale(image)
        enhanced = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (self.config.morphology_kernel, self.config.morphology_kernel),
        )
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        height, width = gray.shape
        max_area = height * width * self.config.maximum_area_ratio
        candidates: list[tuple[int, int, int, int, float, float, float]] = []
        for contour in contours:
            contour_area = float(cv2.contourArea(contour))
            if not self.config.minimum_area <= contour_area <= max_area:
                continue
            x, y, box_width, box_height = cv2.boundingRect(contour)
            if (x <= self.config.border_margin or y <= self.config.border_margin or
                    x + box_width >= width - self.config.border_margin or
                    y + box_height >= height - self.config.border_margin):
                continue
            aspect = box_width / max(box_height, 1)
            if not self.config.minimum_aspect_ratio <= aspect <= self.config.maximum_aspect_ratio:
                continue
            rotated = cv2.minAreaRect(contour)
            angle = float(rotated[2])
            contour_mask = np.zeros_like(gray)
            cv2.drawContours(contour_mask, [contour], -1, 255, cv2.FILLED)
            intensity = float(cv2.mean(gray, mask=contour_mask)[0])
            candidates.append((x, y, box_width, box_height, angle, intensity, contour_area))
        candidates.sort(key=lambda item: (item[1], item[0]))
        detections = []
        for index, (x, y, box_width, box_height, angle, intensity, _) in enumerate(candidates, start=1):
            detections.append(ComponentDetection(
                detection_id=f"contour-{index:04d}", label="generic_component",
                box=BoundingBox(float(x), float(y), float(x + box_width), float(y + box_height)),
                orientation_degrees=angle, mean_intensity=intensity, confidence=None,
                source="classical_contour",
            ))
        return tuple(detections)


class YoloComponentDetector:
    """Adapter for a separately trained component detector; no weights are bundled."""

    def __init__(self, weights: str, confidence: float = 0.25, model_factory=None):
        if not weights:
            raise ValueError("Component model weights are required")
        if not 0 <= confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if model_factory is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("Ultralytics is not installed. Run: pip install -e '.[ml]'") from exc
            model_factory = YOLO
        self.model: Any = model_factory(weights)
        self.confidence = confidence

    def detect(self, image: np.ndarray) -> tuple[ComponentDetection, ...]:
        validate_image(image)
        results = self.model.predict(source=image, conf=self.confidence, save=False, verbose=False)
        if not results:
            return ()
        result = results[0]
        names = result.names
        xyxy = result.boxes.xyxy.cpu().tolist()
        scores = result.boxes.conf.cpu().tolist()
        classes = result.boxes.cls.cpu().tolist()
        detections: list[ComponentDetection] = []
        for index, (coords, score, class_value) in enumerate(zip(xyxy, scores, classes, strict=True), start=1):
            class_id = int(class_value)
            label = str(names[class_id])
            detections.append(ComponentDetection(
                detection_id=f"yolo-{index:04d}", label=label,
                box=BoundingBox(*map(float, coords)), confidence=float(score), source="yolo_component",
            ))
        return tuple(detections)
