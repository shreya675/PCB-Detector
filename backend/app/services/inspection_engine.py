from __future__ import annotations

from dataclasses import replace

import cv2
import numpy as np

from src.cv.alignment import align_to_reference
from src.cv.preprocessing import validate_image
from src.inspection.comparison import compare_components
from src.inspection.detectors import ContourComponentDetector
from src.inspection.template_rules import postprocess
from src.inspection.trace_analysis import analyze_trace_differences

from .contracts import DefectDetector, DefectFinding, InspectionOutcome
from .severity import SeverityPolicy

COLORS = {"critical": (0, 0, 220), "major": (0, 140, 255), "minor": (0, 190, 190)}


class InspectionProcessingError(RuntimeError):
    pass


class InspectionEngine:
    def __init__(self, detector: DefectDetector, policy: SeverityPolicy, reference_analysis: bool = True,
                 postprocess_enabled: bool = True, nms_iou: float = 0.2, box_scale: float = 1.15):
        self.detector = detector
        self.policy = policy
        self.reference_analysis = reference_analysis
        self.postprocess_enabled = postprocess_enabled
        self.nms_iou = nms_iou
        self.box_scale = box_scale

    def _postprocess(self, findings: list[DefectFinding], shape: tuple[int, ...]) -> list[DefectFinding]:
        """Class-agnostic NMS + box scaling, the same chain validated on the DeepPCB test split."""
        if not self.postprocess_enabled or not findings:
            return findings
        height, width = shape[:2]
        refined = postprocess([(item.defect_type, item.confidence or 0.0, item.bbox) for item in findings],
                              nms_iou=self.nms_iou, box_scale=self.box_scale)
        result = []
        for class_name, score, box in refined:
            original = next((item for item in findings
                             if item.defect_type == class_name and (item.confidence or 0.0) == score), None)
            if original is None:
                continue
            x1, y1, x2, y2 = box
            clamped = (max(0.0, x1), max(0.0, y1), min(float(width), x2), min(float(height), y2))
            metadata = dict(original.metadata or {})
            metadata["postprocessed"] = True
            result.append((findings.index(original), replace(original, bbox=clamped, metadata=metadata)))
        return [item for _, item in sorted(result, key=lambda pair: pair[0])]  # keep detector order

    def _reference_findings(self, reference: np.ndarray, aligned: np.ndarray, valid_mask: np.ndarray) -> list[DefectFinding]:
        findings: list[DefectFinding] = []
        component_detector = ContourComponentDetector()
        # Only compare fully visible candidates, with a margin from warped borders.
        safe_mask = cv2.erode(valid_mask, np.ones((7, 7), dtype=np.uint8),
                              borderType=cv2.BORDER_CONSTANT, borderValue=0)

        def visible(items):
            result = []
            for item in items:
                box = item.box
                x1, y1 = int(np.floor(box.x_min)), int(np.floor(box.y_min))
                x2, y2 = int(np.ceil(box.x_max)), int(np.ceil(box.y_max))
                region = safe_mask[y1:y2, x1:x2]
                if region.size and np.all(region > 0):
                    result.append(item)
            return tuple(result)

        comparison = compare_components(visible(component_detector.detect(reference)),
                                        visible(component_detector.detect(aligned)))
        for item in comparison.missing:
            findings.append(DefectFinding("missing_component", (item.box.x_min, item.box.y_min,
                                                                 item.box.x_max, item.box.y_max),
                                          None, "reference_component_contour",
                                          metadata={"heuristic": True}))
        for match in comparison.misplaced:
            box = match.observed.box
            findings.append(DefectFinding("misaligned_component", (box.x_min, box.y_min, box.x_max, box.y_max),
                                          None, "reference_component_contour",
                                          metadata={"heuristic": True, "center_distance": match.center_distance}))
        for item in comparison.unexpected:
            findings.append(DefectFinding("unexpected_component", (item.box.x_min, item.box.y_min,
                                                                    item.box.x_max, item.box.y_max),
                                          None, "reference_component_contour",
                                          metadata={"heuristic": True}))
        traces = analyze_trace_differences(reference, aligned, valid_mask)
        for candidate in traces.candidates:
            box = candidate.box
            findings.append(DefectFinding(candidate.category, (box.x_min, box.y_min, box.x_max, box.y_max),
                                          None, candidate.method,
                                          metadata={"heuristic": True,
                                                    "evidence_strength": candidate.evidence_strength}))
        return findings

    def inspect(self, test_image: np.ndarray, reference_image: np.ndarray | None = None) -> InspectionOutcome:
        validate_image(test_image, "test")
        aligned = test_image
        alignment_quality = None
        reference_findings = []
        if reference_image is not None and self.reference_analysis:
            alignment = align_to_reference(reference_image, test_image)
            alignment_quality = alignment.quality_dict()
            if not alignment.success:
                raise InspectionProcessingError(f"Reference registration failed: {alignment.reason}")
            aligned = alignment.aligned_image
            reference_findings = self._reference_findings(reference_image, aligned, alignment.valid_mask)
        # All boxes and annotations share the same image coordinate frame.
        findings = self._postprocess(list(self.detector.detect(aligned)), aligned.shape) + reference_findings
        findings = [replace(item, severity=self.policy.severity_for(item.defect_type)) for item in findings]
        status, counts = self.policy.decide([item.severity for item in findings if item.severity])
        annotated = aligned.copy()
        for item in findings:
            x1, y1, x2, y2 = map(round, item.bbox)
            color = COLORS[item.severity]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{item.defect_type} · {item.severity}"
            if item.confidence is not None:
                label += f" · {item.confidence:.2f}"
            cv2.putText(annotated, label, (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                        0.45, color, 1, cv2.LINE_AA)
        summary = {"defect_count": len(findings), "severity_counts": counts,
                   "reference_comparison": alignment_quality is not None,
                   "coordinate_frame": "reference" if alignment_quality else "test",
                   "heuristic_count": sum(bool((item.metadata or {}).get("heuristic")) for item in findings),
                   "prototype_notice": "Academic/research prototype; not industrially certified."}
        if alignment_quality and alignment_quality["overlap_ratio"] < 0.999:
            summary["coverage_warning"] = "Only the overlapping board area was compared; uncovered areas require review."
            if status == "PASS":
                status = "PASS WITH WARNING"
        return InspectionOutcome(status, tuple(findings), counts, annotated, alignment_quality, summary)
