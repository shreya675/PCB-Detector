from __future__ import annotations

import cv2
import numpy as np

from .comparison import ComparisonResult
from .components import ComponentDetection


def _box(image: np.ndarray, detection: ComponentDetection, color: tuple[int, int, int], label: str) -> None:
    box = detection.box
    first, second = (round(box.x_min), round(box.y_min)), (round(box.x_max), round(box.y_max))
    cv2.rectangle(image, first, second, color, 2)
    cv2.putText(image, label, (first[0], max(16, first[1] - 5)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)


def render_comparison(reference: np.ndarray, aligned_test: np.ndarray,
                      result: ComparisonResult) -> tuple[np.ndarray, np.ndarray]:
    expected, observed = reference.copy(), aligned_test.copy()
    for match in result.matches:
        color = (0, 165, 255) if match.status == "misplaced" else (60, 180, 75)
        _box(expected, match.reference, color, match.status)
        _box(observed, match.observed, color, match.status)
    for component in result.missing:
        _box(expected, component, (0, 0, 255), "missing")
    for component in result.unexpected:
        _box(observed, component, (180, 60, 180), "unexpected")
    return expected, observed
