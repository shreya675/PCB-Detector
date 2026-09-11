import unittest

import cv2
import numpy as np

from src.cv.difference import DifferenceConfig, compute_difference


class DifferenceTests(unittest.TestCase):
    def test_visible_change_creates_region(self):
        reference = np.full((160, 200, 3), 210, dtype=np.uint8)
        test = reference.copy()
        cv2.rectangle(test, (70, 55), (110, 95), (20, 20, 20), -1)
        result = compute_difference(reference, test, config=DifferenceConfig(threshold=25, minimum_area=100))
        self.assertEqual(len(result.regions), 1)
        region = result.regions[0]
        self.assertLessEqual(region.x, 72)
        self.assertGreaterEqual(region.width, 38)
        self.assertGreater(result.changed_pixel_ratio, 0)

    def test_valid_mask_excludes_border_change(self):
        reference = np.full((100, 100), 200, dtype=np.uint8)
        test = reference.copy()
        test[:, :20] = 0
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[:, 20:] = 255
        result = compute_difference(reference, test, mask, DifferenceConfig(threshold=10, minimum_area=5))
        self.assertEqual(len(result.regions), 0)
        self.assertEqual(result.changed_pixel_ratio, 0.0)

    def test_dimension_mismatch_is_rejected(self):
        with self.assertRaises(ValueError):
            compute_difference(np.zeros((32, 32), dtype=np.uint8), np.zeros((40, 32), dtype=np.uint8))
