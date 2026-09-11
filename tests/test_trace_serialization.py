import json
import unittest

import cv2
import numpy as np

from src.inspection.trace_analysis import TraceAnalysisConfig, analyze_trace_differences


class TraceSerializationTests(unittest.TestCase):
    def test_result_contains_candidate_disclaimer_fields(self):
        reference = np.zeros((80, 120), dtype=np.uint8)
        cv2.line(reference, (10, 40), (110, 40), 255, 5)
        test = reference.copy()
        cv2.rectangle(test, (50, 35), (65, 45), 0, -1)
        result = analyze_trace_differences(
            reference, test,
            config=TraceAnalysisConfig(threshold=127, morphology_kernel=1,
                                       alignment_tolerance=1, minimum_region_area=5),
        )
        encoded = json.dumps(result.json_dict())
        self.assertIn("broken_trace_candidate", encoded)
        self.assertIn("evidence_strength", encoded)
