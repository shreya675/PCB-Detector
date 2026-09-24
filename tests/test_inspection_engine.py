import unittest

import numpy as np

from backend.app.services.contracts import DefectFinding
from backend.app.services.inspection_engine import InspectionEngine
from backend.app.services.severity import SeverityPolicy


class FakeDetector:
    model_version = "test:model"
    def __init__(self, findings=()): self.findings = findings
    def detect(self, image): return self.findings


class InspectionEngineTests(unittest.TestCase):
    def setUp(self):
        self.policy = SeverityPolicy({"short_circuit": "critical", "spur": "minor"})
        self.image = np.zeros((80, 100, 3), dtype=np.uint8)

    def test_no_defect_case_passes(self):
        outcome = InspectionEngine(FakeDetector(), self.policy, reference_analysis=False).inspect(self.image)
        self.assertEqual(outcome.status, "PASS")
        self.assertEqual(outcome.summary["defect_count"], 0)

    def test_multiple_defects_fail(self):
        findings = (
            DefectFinding("spur", (1, 1, 10, 10), 0.7, "test"),
            DefectFinding("short_circuit", (20, 20, 30, 30), 0.9, "test"),
        )
        outcome = InspectionEngine(FakeDetector(findings), self.policy, reference_analysis=False).inspect(self.image)
        self.assertEqual(outcome.status, "FAIL")
        self.assertEqual(outcome.findings[1].severity, "critical")

    def test_confidence_is_preserved(self):
        finding = DefectFinding("spur", (1, 1, 10, 10), 0.73, "test")
        outcome = InspectionEngine(FakeDetector((finding,)), self.policy, reference_analysis=False).inspect(self.image)
        self.assertEqual(outcome.findings[0].confidence, 0.73)


class PostprocessTests(unittest.TestCase):
    def setUp(self):
        self.policy = SeverityPolicy({"short_circuit": "critical", "spur": "minor"})
        self.image = np.zeros((80, 100, 3), dtype=np.uint8)

    def test_overlapping_duplicates_collapse_to_highest_score(self):
        findings = (
            DefectFinding("spur", (10, 10, 30, 30), 0.6, "yolo_defect"),
            DefectFinding("short_circuit", (11, 11, 31, 31), 0.9, "yolo_defect"),
        )
        outcome = InspectionEngine(FakeDetector(findings), self.policy, reference_analysis=False).inspect(self.image)
        self.assertEqual(len(outcome.findings), 1)
        self.assertEqual(outcome.findings[0].defect_type, "short_circuit")
        self.assertTrue(outcome.findings[0].metadata["postprocessed"])

    def test_boxes_are_scaled_and_clamped_to_image(self):
        finding = DefectFinding("spur", (0, 0, 20, 20), 0.8, "yolo_defect")
        engine = InspectionEngine(FakeDetector((finding,)), self.policy, reference_analysis=False, box_scale=1.5)
        box = engine.inspect(self.image).findings[0].bbox
        self.assertEqual(box[0], 0.0)
        self.assertEqual(box[1], 0.0)
        self.assertAlmostEqual(box[2], 25.0)

    def test_postprocess_can_be_disabled(self):
        findings = (
            DefectFinding("spur", (10, 10, 30, 30), 0.6, "yolo_defect"),
            DefectFinding("short_circuit", (11, 11, 31, 31), 0.9, "yolo_defect"),
        )
        engine = InspectionEngine(FakeDetector(findings), self.policy, reference_analysis=False, postprocess_enabled=False)
        self.assertEqual(len(engine.inspect(self.image).findings), 2)
