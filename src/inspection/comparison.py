from __future__ import annotations

import math
from dataclasses import dataclass

from .components import ComponentDetection


@dataclass(frozen=True)
class ComparisonConfig:
    maximum_center_distance: float = 45.0
    misplaced_center_distance: float = 10.0
    maximum_area_log_ratio: float = 0.80
    misplaced_area_log_ratio: float = 0.30
    maximum_orientation_difference: float = 35.0
    misplaced_orientation_difference: float = 15.0
    center_weight: float = 0.60
    area_weight: float = 0.25
    orientation_weight: float = 0.15

    def validate(self) -> None:
        if self.maximum_center_distance <= 0 or self.misplaced_center_distance < 0:
            raise ValueError("Center-distance thresholds are invalid")
        if self.misplaced_center_distance > self.maximum_center_distance:
            raise ValueError("Misplaced distance cannot exceed maximum match distance")
        if self.maximum_area_log_ratio <= 0 or self.maximum_orientation_difference < 0:
            raise ValueError("Area and orientation thresholds are invalid")
        if not math.isclose(self.center_weight + self.area_weight + self.orientation_weight, 1.0, abs_tol=1e-6):
            raise ValueError("Comparison weights must sum to 1")


@dataclass(frozen=True)
class ComponentMatch:
    reference: ComponentDetection
    observed: ComponentDetection
    score: float
    center_distance: float
    area_log_ratio: float
    orientation_difference: float
    status: str


@dataclass(frozen=True)
class ComparisonResult:
    matches: tuple[ComponentMatch, ...]
    missing: tuple[ComponentDetection, ...]
    unexpected: tuple[ComponentDetection, ...]

    @property
    def misplaced(self) -> tuple[ComponentMatch, ...]:
        return tuple(match for match in self.matches if match.status == "misplaced")

    @property
    def matched(self) -> tuple[ComponentMatch, ...]:
        return tuple(match for match in self.matches if match.status == "matched")

    def summary(self) -> dict[str, int]:
        return {
            "reference_components": len(self.matches) + len(self.missing),
            "observed_components": len(self.matches) + len(self.unexpected),
            "matched": len(self.matched), "misplaced": len(self.misplaced),
            "missing": len(self.missing), "unexpected": len(self.unexpected),
        }


def _angle_difference(first: float, second: float) -> float:
    difference = abs(first - second) % 180.0
    return min(difference, 180.0 - difference)


def _candidate(reference: ComponentDetection, observed: ComponentDetection,
               config: ComparisonConfig) -> tuple[float, float, float, float] | None:
    if (reference.label != "generic_component" and observed.label != "generic_component" and
            reference.label != observed.label):
        return None
    rx, ry = reference.box.center
    ox, oy = observed.box.center
    center_distance = math.hypot(rx - ox, ry - oy)
    area_log_ratio = abs(math.log(max(observed.box.area, 1e-9) / max(reference.box.area, 1e-9)))
    orientation_difference = _angle_difference(reference.orientation_degrees, observed.orientation_degrees)
    if (center_distance > config.maximum_center_distance or
            area_log_ratio > config.maximum_area_log_ratio or
            orientation_difference > config.maximum_orientation_difference):
        return None
    score = (
        config.center_weight * center_distance / config.maximum_center_distance +
        config.area_weight * area_log_ratio / config.maximum_area_log_ratio +
        config.orientation_weight * orientation_difference / max(config.maximum_orientation_difference, 1e-9)
    )
    return score, center_distance, area_log_ratio, orientation_difference


def compare_components(reference_components: tuple[ComponentDetection, ...],
                       observed_components: tuple[ComponentDetection, ...],
                       config: ComparisonConfig | None = None) -> ComparisonResult:
    config = config or ComparisonConfig()
    config.validate()
    for detection in (*reference_components, *observed_components):
        detection.validate()
    edges: list[tuple[float, int, int, float, float, float]] = []
    for ref_index, reference in enumerate(reference_components):
        for obs_index, observed in enumerate(observed_components):
            candidate = _candidate(reference, observed, config)
            if candidate:
                score, distance, area_ratio, angle = candidate
                edges.append((score, ref_index, obs_index, distance, area_ratio, angle))
    edges.sort(key=lambda edge: edge[0])
    used_reference: set[int] = set()
    used_observed: set[int] = set()
    matches: list[ComponentMatch] = []
    for score, ref_index, obs_index, distance, area_ratio, angle in edges:
        if ref_index in used_reference or obs_index in used_observed:
            continue
        used_reference.add(ref_index)
        used_observed.add(obs_index)
        status = "misplaced" if (
            distance > config.misplaced_center_distance or
            area_ratio > config.misplaced_area_log_ratio or
            angle > config.misplaced_orientation_difference
        ) else "matched"
        matches.append(ComponentMatch(reference_components[ref_index], observed_components[obs_index],
                                      score, distance, area_ratio, angle, status))
    matches.sort(key=lambda item: item.reference.detection_id)
    missing = tuple(item for index, item in enumerate(reference_components) if index not in used_reference)
    unexpected = tuple(item for index, item in enumerate(observed_components) if index not in used_observed)
    return ComparisonResult(tuple(matches), missing, unexpected)
