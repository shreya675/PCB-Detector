import unittest

import cv2
import numpy as np

from src.inspection.trace_analysis import (
    TraceAnalysisConfig,
    analyze_trace_differences,
    segment_copper,
    skeletonize,
)

CONFIG = TraceAnalysisConfig(threshold=127, morphology_kernel=1, alignment_tolerance=1,
                             contact_radius=5, minimum_region_area=5)


class TraceAnalysisTests(unittest.TestCase):
    def test_no_change_produces_no_candidates(self):
        image = np.zeros((120, 180), dtype=np.uint8)
        cv2.line(image, (20, 60), (160, 60), 255, 5)
        result = analyze_trace_differences(image, image.copy(), config=CONFIG)
        self.assertEqual(result.candidates, ())

    def test_gap_produces_broken_trace_candidate(self):
        reference = np.zeros((120, 180), dtype=np.uint8)
        cv2.line(reference, (20, 60), (160, 60), 255, 5)
        test = reference.copy()
        cv2.rectangle(test, (82, 55), (98, 65), 0, -1)
        result = analyze_trace_differences(reference, test, config=CONFIG)
        categories = [item.category for item in result.candidates]
        self.assertIn("broken_trace_candidate", categories)

    def test_connector_between_regions_produces_bridge_candidate(self):
        reference = np.zeros((140, 180), dtype=np.uint8)
        cv2.line(reference, (20, 50), (160, 50), 255, 5)
        cv2.line(reference, (20, 80), (160, 80), 255, 5)
        test = reference.copy()
        cv2.line(test, (90, 50), (90, 80), 255, 5)
        config = TraceAnalysisConfig(threshold=127, morphology_kernel=1, alignment_tolerance=1,
                                     contact_radius=6, minimum_region_area=5)
        result = analyze_trace_differences(reference, test, config=config)
        bridges = [item for item in result.candidates if item.category == "bridge_candidate"]
        self.assertEqual(len(bridges), 1)
        self.assertGreaterEqual(bridges[0].reference_regions_contacted, 2)

    def test_isolated_addition_is_spurious_candidate(self):
        reference = np.zeros((120, 180), dtype=np.uint8)
        cv2.line(reference, (20, 40), (160, 40), 255, 5)
        test = reference.copy()
        cv2.rectangle(test, (80, 85), (95, 95), 255, -1)
        result = analyze_trace_differences(reference, test, config=CONFIG)
        self.assertIn("spurious_copper_candidate", [item.category for item in result.candidates])

    def test_valid_mask_excludes_change(self):
        reference = np.zeros((100, 120), dtype=np.uint8)
        test = reference.copy()
        cv2.rectangle(test, (5, 5), (20, 20), 255, -1)
        valid = np.full((100, 120), 255, dtype=np.uint8)
        valid[:30, :30] = 0
        result = analyze_trace_differences(reference, test, valid, CONFIG)
        self.assertEqual(result.candidates, ())

    def test_skeleton_is_thinner_than_mask(self):
        mask = np.zeros((80, 100), dtype=np.uint8)
        cv2.rectangle(mask, (10, 30), (90, 50), 255, -1)
        skeleton = skeletonize(mask)
        self.assertGreater(cv2.countNonZero(skeleton), 0)
        self.assertLess(cv2.countNonZero(skeleton), cv2.countNonZero(mask))

    def test_dark_copper_mode(self):
        image = np.full((64, 64), 255, dtype=np.uint8)
        cv2.rectangle(image, (20, 20), (40, 40), 0, -1)
        mask = segment_copper(image, TraceAnalysisConfig(threshold=127, copper_is_bright=False, morphology_kernel=1))
        self.assertEqual(int(mask[30, 30]), 255)
