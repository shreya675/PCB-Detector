from __future__ import annotations

from dataclasses import dataclass

from .components import BoundingBox
from .trace_analysis import TraceCandidate


@dataclass(frozen=True)
class InspectionEvidence:
    evidence_id: str
    category: str
    box: BoundingBox
    evidence_strength: float
    methods: tuple[str, ...]
    source_ids: tuple[str, ...]


def intersection_over_union(first: BoundingBox, second: BoundingBox) -> float:
    x1, y1 = max(first.x_min, second.x_min), max(first.y_min, second.y_min)
    x2, y2 = min(first.x_max, second.x_max), min(first.y_max, second.y_max)
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    union = first.area + second.area - intersection
    return intersection / union if union > 0 else 0.0


def _union_box(first: BoundingBox, second: BoundingBox) -> BoundingBox:
    return BoundingBox(min(first.x_min, second.x_min), min(first.y_min, second.y_min),
                       max(first.x_max, second.x_max), max(first.y_max, second.y_max))


def fuse_trace_evidence(candidates: tuple[TraceCandidate, ...], iou_threshold: float = 0.35) -> tuple[InspectionEvidence, ...]:
    if not 0 <= iou_threshold <= 1:
        raise ValueError("iou_threshold must be between 0 and 1")
    fused: list[InspectionEvidence] = []
    for candidate in sorted(candidates, key=lambda item: item.evidence_strength, reverse=True):
        match_index = next((index for index, item in enumerate(fused)
                            if item.category == candidate.category and
                            intersection_over_union(item.box, candidate.box) >= iou_threshold), None)
        if match_index is None:
            fused.append(InspectionEvidence(
                f"evidence-{len(fused) + 1:04d}", candidate.category, candidate.box,
                candidate.evidence_strength, (candidate.method,), (candidate.candidate_id,),
            ))
        else:
            previous = fused[match_index]
            fused[match_index] = InspectionEvidence(
                previous.evidence_id, previous.category, _union_box(previous.box, candidate.box),
                max(previous.evidence_strength, candidate.evidence_strength),
                tuple(sorted({*previous.methods, candidate.method})),
                (*previous.source_ids, candidate.candidate_id),
            )
    return tuple(sorted(fused, key=lambda item: item.evidence_id))
