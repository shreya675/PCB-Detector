import unittest

from src.inspection.components import BoundingBox
from src.inspection.evidence import fuse_trace_evidence, intersection_over_union
from src.inspection.trace_analysis import TraceCandidate


def candidate(identifier, box, category="broken_trace_candidate", strength=0.5):
    return TraceCandidate(identifier, category, box, 20, 18.0, strength, "test_method")


class EvidenceFusionTests(unittest.TestCase):
    def test_overlapping_same_category_is_fused(self):
        items = (
            candidate("a", BoundingBox(0, 0, 20, 20), strength=0.4),
            candidate("b", BoundingBox(2, 2, 21, 21), strength=0.8),
        )
        result = fuse_trace_evidence(items)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].evidence_strength, 0.8)
        self.assertEqual(result[0].source_ids, ("b", "a"))

    def test_different_categories_are_not_fused(self):
        box = BoundingBox(0, 0, 20, 20)
        result = fuse_trace_evidence((candidate("a", box), candidate("b", box, "bridge_candidate")))
        self.assertEqual(len(result), 2)

    def test_iou_handles_disjoint_boxes(self):
        self.assertEqual(intersection_over_union(BoundingBox(0, 0, 5, 5), BoundingBox(10, 10, 15, 15)), 0.0)

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            fuse_trace_evidence((), 1.5)
