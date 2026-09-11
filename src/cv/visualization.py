from __future__ import annotations

import cv2
import numpy as np

from .difference import DifferenceRegion


def draw_difference_regions(image: np.ndarray, regions: tuple[DifferenceRegion, ...]) -> np.ndarray:
    annotated = image.copy()
    for index, region in enumerate(regions, start=1):
        cv2.rectangle(annotated, (region.x, region.y),
                      (region.x + region.width, region.y + region.height), (0, 0, 255), 2)
        cv2.putText(annotated, f"difference {index}", (region.x, max(18, region.y - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
    return annotated
