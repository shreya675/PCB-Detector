import unittest

import cv2
import numpy as np

from src.inspection.detectors import ContourComponentDetector, ContourDetectorConfig


class ComponentDetectorTests(unittest.TestCase):
    def test_detects_dark_component_candidates(self):
        image = np.full((240, 320, 3), 220, dtype=np.uint8)
        cv2.rectangle(image, (45, 55), (85, 75), (20, 20, 20), -1)
        cv2.rectangle(image, (180, 140), (215, 165), (35, 35, 35), -1)
        detector = ContourComponentDetector(ContourDetectorConfig(minimum_area=200))
        detections = detector.detect(image)
        self.assertEqual(len(detections), 2)
        self.assertTrue(all(item.label == "generic_component" for item in detections))
        self.assertTrue(all(item.confidence is None for item in detections))

    def test_rejects_border_regions(self):
        image = np.full((160, 200, 3), 220, dtype=np.uint8)
        cv2.rectangle(image, (0, 20), (30, 60), (0, 0, 0), -1)
        detector = ContourComponentDetector(ContourDetectorConfig(minimum_area=100))
        self.assertEqual(detector.detect(image), ())
