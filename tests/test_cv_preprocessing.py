import unittest

import numpy as np

from src.cv.preprocessing import PreprocessConfig, preprocess_for_features, validate_image


class PreprocessingTests(unittest.TestCase):
    def test_color_image_becomes_uint8_grayscale(self):
        image = np.full((64, 80, 3), 1000, dtype=np.uint16)
        output = preprocess_for_features(image)
        self.assertEqual(output.shape, (64, 80))
        self.assertEqual(output.dtype, np.uint8)

    def test_invalid_channel_count_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_image(np.zeros((64, 64, 2), dtype=np.uint8))

    def test_nan_image_is_rejected(self):
        image = np.zeros((32, 32), dtype=np.float32)
        image[0, 0] = np.nan
        with self.assertRaises(ValueError):
            validate_image(image)

    def test_even_blur_kernel_is_rejected(self):
        with self.assertRaises(ValueError):
            PreprocessConfig(gaussian_kernel=4).validate()
