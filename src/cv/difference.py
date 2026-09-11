from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .preprocessing import to_grayscale, validate_image


@dataclass(frozen=True)
class DifferenceConfig:
    threshold: int | None = None
    blur_kernel: int = 5
    morphology_kernel: int = 5
    minimum_area: int = 25

    def validate(self) -> None:
        if self.threshold is not None and not 0 <= self.threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")
        if self.blur_kernel < 1 or self.blur_kernel % 2 == 0:
            raise ValueError("blur_kernel must be a positive odd integer")
        if self.morphology_kernel < 1 or self.minimum_area < 1:
            raise ValueError("morphology_kernel and minimum_area must be positive")


@dataclass(frozen=True)
class DifferenceRegion:
    x: int
    y: int
    width: int
    height: int
    area: float
    mean_difference: float


@dataclass(frozen=True)
class DifferenceResult:
    absolute_difference: np.ndarray
    binary_mask: np.ndarray
    regions: tuple[DifferenceRegion, ...]
    changed_pixel_ratio: float


def compute_difference(reference: np.ndarray, aligned_test: np.ndarray,
                       valid_mask: np.ndarray | None = None,
                       config: DifferenceConfig | None = None) -> DifferenceResult:
    config = config or DifferenceConfig()
    config.validate()
    validate_image(reference, "reference")
    validate_image(aligned_test, "aligned_test")
    if reference.shape[:2] != aligned_test.shape[:2]:
        raise ValueError("Reference and aligned test images must have identical dimensions")
    reference_gray, test_gray = to_grayscale(reference), to_grayscale(aligned_test)
    absolute = cv2.absdiff(reference_gray, test_gray)
    if config.blur_kernel > 1:
        absolute = cv2.GaussianBlur(absolute, (config.blur_kernel, config.blur_kernel), 0)
    if valid_mask is not None:
        if valid_mask.shape != absolute.shape:
            raise ValueError("valid_mask must match image dimensions")
        absolute = cv2.bitwise_and(absolute, absolute, mask=(valid_mask > 0).astype(np.uint8) * 255)
    mode = cv2.THRESH_BINARY | (cv2.THRESH_OTSU if config.threshold is None else 0)
    threshold_value = 0 if config.threshold is None else config.threshold
    _, binary = cv2.threshold(absolute, threshold_value, 255, mode)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (config.morphology_kernel, config.morphology_kernel))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions: list[DifferenceRegion] = []
    for contour in contours:
        area = float(cv2.contourArea(contour))
        if area < config.minimum_area:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        contour_mask = np.zeros(binary.shape, dtype=np.uint8)
        cv2.drawContours(contour_mask, [contour], -1, 255, thickness=cv2.FILLED)
        mean_difference = float(cv2.mean(absolute, mask=contour_mask)[0])
        regions.append(DifferenceRegion(x, y, width, height, area, mean_difference))
    regions.sort(key=lambda item: item.area, reverse=True)
    denominator = np.count_nonzero(valid_mask) if valid_mask is not None else binary.size
    changed_ratio = float(np.count_nonzero(binary)) / max(int(denominator), 1)
    return DifferenceResult(absolute, binary, tuple(regions), changed_ratio)
