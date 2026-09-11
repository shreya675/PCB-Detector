from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np

from src.cv.preprocessing import to_grayscale, validate_image

from .components import BoundingBox


@dataclass(frozen=True)
class TraceAnalysisConfig:
    threshold: int | None = None
    copper_is_bright: bool = True
    morphology_kernel: int = 3
    alignment_tolerance: int = 2
    contact_radius: int = 5
    minimum_region_area: int = 12

    def validate(self) -> None:
        if self.threshold is not None and not 0 <= self.threshold <= 255:
            raise ValueError("threshold must be between 0 and 255")
        if self.morphology_kernel < 1 or self.alignment_tolerance < 0:
            raise ValueError("morphology_kernel must be positive and tolerance non-negative")
        if self.contact_radius < 1 or self.minimum_region_area < 1:
            raise ValueError("contact_radius and minimum_region_area must be positive")


@dataclass(frozen=True)
class TraceCandidate:
    candidate_id: str
    category: str
    box: BoundingBox
    pixel_area: int
    contour_area: float
    evidence_strength: float
    method: str
    reference_regions_contacted: int = 0


@dataclass(frozen=True)
class TraceAnalysisResult:
    reference_copper_mask: np.ndarray
    test_copper_mask: np.ndarray
    reference_skeleton: np.ndarray
    missing_copper_mask: np.ndarray
    added_copper_mask: np.ndarray
    candidates: tuple[TraceCandidate, ...]
    valid_pixel_count: int

    def summary(self) -> dict[str, int]:
        categories: dict[str, int] = {
            "broken_trace_candidate": 0,
            "bridge_candidate": 0,
            "spurious_copper_candidate": 0,
        }
        for candidate in self.candidates:
            categories[candidate.category] = categories.get(candidate.category, 0) + 1
        return {"candidate_count": len(self.candidates), "valid_pixel_count": self.valid_pixel_count, **categories}

    def json_dict(self) -> dict:
        return {"summary": self.summary(), "candidates": [asdict(item) for item in self.candidates]}


def segment_copper(image: np.ndarray, config: TraceAnalysisConfig | None = None) -> np.ndarray:
    config = config or TraceAnalysisConfig()
    config.validate()
    validate_image(image)
    gray = to_grayscale(image)
    threshold_type = cv2.THRESH_BINARY if config.copper_is_bright else cv2.THRESH_BINARY_INV
    threshold_value = 0 if config.threshold is None else config.threshold
    if config.threshold is None:
        threshold_type |= cv2.THRESH_OTSU
    _, mask = cv2.threshold(gray, threshold_value, 255, threshold_type)
    if config.morphology_kernel > 1:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (config.morphology_kernel, config.morphology_kernel),
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def skeletonize(binary_mask: np.ndarray) -> np.ndarray:
    if binary_mask.ndim != 2 or binary_mask.dtype != np.uint8:
        raise ValueError("skeletonize expects a uint8 single-channel mask")
    image = np.where(binary_mask > 0, 255, 0).astype(np.uint8)
    skeleton = np.zeros_like(image)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while cv2.countNonZero(image):
        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, element)
        residue = cv2.subtract(image, opened)
        skeleton = cv2.bitwise_or(skeleton, residue)
        image = cv2.erode(image, element, borderType=cv2.BORDER_CONSTANT, borderValue=0)
    return skeleton


def _contour_regions(mask: np.ndarray, minimum_area: int):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    items = []
    for contour in contours:
        contour_area = float(cv2.contourArea(contour))
        x, y, width, height = cv2.boundingRect(contour)
        region_mask = np.zeros_like(mask)
        cv2.drawContours(region_mask, [contour], -1, 255, cv2.FILLED)
        pixel_area = int(cv2.countNonZero(region_mask))
        if pixel_area >= minimum_area:
            items.append((x, y, width, height, contour_area, pixel_area, region_mask))
    return sorted(items, key=lambda item: (item[1], item[0]))


def analyze_trace_differences(reference: np.ndarray, aligned_test: np.ndarray,
                              valid_mask: np.ndarray | None = None,
                              config: TraceAnalysisConfig | None = None) -> TraceAnalysisResult:
    config = config or TraceAnalysisConfig()
    config.validate()
    validate_image(reference, "reference")
    validate_image(aligned_test, "aligned_test")
    if reference.shape[:2] != aligned_test.shape[:2]:
        raise ValueError("Reference and aligned test dimensions must match")
    height, width = reference.shape[:2]
    if valid_mask is None:
        valid = np.full((height, width), 255, dtype=np.uint8)
    else:
        if valid_mask.shape != (height, width):
            raise ValueError("valid_mask dimensions must match the images")
        valid = np.where(valid_mask > 0, 255, 0).astype(np.uint8)

    reference_mask = cv2.bitwise_and(segment_copper(reference, config), valid)
    test_mask = cv2.bitwise_and(segment_copper(aligned_test, config), valid)
    size = 2 * config.alignment_tolerance + 1
    tolerance_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
    supported_test = cv2.dilate(test_mask, tolerance_kernel) if config.alignment_tolerance else test_mask
    supported_reference = cv2.dilate(reference_mask, tolerance_kernel) if config.alignment_tolerance else reference_mask
    missing = cv2.bitwise_and(reference_mask, cv2.bitwise_not(supported_test))
    added = cv2.bitwise_and(test_mask, cv2.bitwise_not(supported_reference))
    skeleton = skeletonize(reference_mask)

    candidates: list[TraceCandidate] = []
    sequence = 1
    skeleton_support = cv2.dilate(skeleton, np.ones((3, 3), dtype=np.uint8))
    for x, y, box_width, box_height, contour_area, pixel_area, region_mask in _contour_regions(
        missing, config.minimum_region_area,
    ):
        if cv2.countNonZero(cv2.bitwise_and(region_mask, skeleton_support)) == 0:
            continue
        strength = min(1.0, pixel_area / max(config.minimum_region_area * 5.0, 1.0))
        candidates.append(TraceCandidate(
            f"trace-{sequence:04d}", "broken_trace_candidate",
            BoundingBox(float(x), float(y), float(x + box_width), float(y + box_height)),
            pixel_area, contour_area, strength, "reference_minus_test_skeleton_overlap",
        ))
        sequence += 1

    _component_count, reference_labels = cv2.connectedComponents(reference_mask)
    contact_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * config.contact_radius + 1, 2 * config.contact_radius + 1),
    )
    for x, y, box_width, box_height, contour_area, pixel_area, region_mask in _contour_regions(
        added, config.minimum_region_area,
    ):
        contact_zone = cv2.dilate(region_mask, contact_kernel)
        contacted = {int(value) for value in np.unique(reference_labels[contact_zone > 0]) if value > 0}
        category = "bridge_candidate" if len(contacted) >= 2 else "spurious_copper_candidate"
        strength = min(1.0, pixel_area / max(config.minimum_region_area * 5.0, 1.0))
        candidates.append(TraceCandidate(
            f"trace-{sequence:04d}", category,
            BoundingBox(float(x), float(y), float(x + box_width), float(y + box_height)),
            pixel_area, contour_area, strength, "test_minus_reference_connectivity",
            len(contacted),
        ))
        sequence += 1

    return TraceAnalysisResult(reference_mask, test_mask, skeleton, missing, added,
                               tuple(candidates), int(cv2.countNonZero(valid)))
