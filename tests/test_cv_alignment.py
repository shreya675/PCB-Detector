import unittest

import cv2
import numpy as np

from src.cv.alignment import AlignmentConfig, align_to_reference


def feature_board() -> np.ndarray:
    image = np.full((420, 560, 3), 235, dtype=np.uint8)
    rng = np.random.default_rng(7)
    for index in range(85):
        center = tuple(int(value) for value in rng.integers([25, 25], [535, 395]))
        radius = int(rng.integers(3, 10))
        color = tuple(int(value) for value in rng.integers(15, 180, size=3))
        cv2.circle(image, center, radius, color, -1)
        if index % 4 == 0:
            cv2.line(image, center, (min(center[0] + 35, 550), min(center[1] + 17, 410)), color, 2)
    cv2.rectangle(image, (18, 18), (542, 402), (20, 80, 20), 3)
    cv2.putText(image, "PCB-AOI-04", (150, 215), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (10, 10, 10), 3)
    return image


class AlignmentTests(unittest.TestCase):
    def test_perspective_image_aligns_to_reference(self):
        reference = feature_board()
        source = np.float32([[0, 0], [559, 0], [559, 419], [0, 419]])
        target = np.float32([[16, 12], [540, 6], [552, 408], [10, 414]])
        forward = cv2.getPerspectiveTransform(source, target)
        test = cv2.warpPerspective(reference, forward, (560, 420), borderValue=(255, 255, 255))
        config = AlignmentConfig(min_matches=20, min_inlier_ratio=0.35, min_overlap_ratio=0.75)
        result = align_to_reference(reference, test, config)
        self.assertTrue(result.success, result.reason)
        self.assertGreaterEqual(result.good_matches, 20)
        self.assertGreater(result.inlier_ratio, 0.35)
        self.assertGreater(result.overlap_ratio, 0.75)
        valid = result.valid_mask > 0
        error = np.mean(cv2.absdiff(reference, result.aligned_image)[valid])
        self.assertLess(error, 18.0)

    def test_blank_images_fail_without_exception(self):
        blank = np.full((128, 128, 3), 255, dtype=np.uint8)
        result = align_to_reference(blank, blank)
        self.assertFalse(result.success)
        self.assertEqual(result.reason, "insufficient_features")
