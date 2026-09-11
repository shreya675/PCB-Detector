from __future__ import annotations

import cv2
import numpy as np

from .trace_analysis import TraceCandidate

COLORS = {
    "broken_trace_candidate": (0, 0, 255),
    "bridge_candidate": (0, 165, 255),
    "spurious_copper_candidate": (180, 60, 180),
}


def render_trace_candidates(image: np.ndarray, candidates: tuple[TraceCandidate, ...]) -> np.ndarray:
    annotated = image.copy()
    for candidate in candidates:
        box = candidate.box
        color = COLORS.get(candidate.category, (255, 0, 0))
        first = (round(box.x_min), round(box.y_min))
        second = (round(box.x_max), round(box.y_max))
        cv2.rectangle(annotated, first, second, color, 2)
        label = candidate.category.replace("_candidate", "")
        cv2.putText(annotated, label, (first[0], max(16, first[1] - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)
    return annotated
