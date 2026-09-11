import tempfile
import unittest
from pathlib import Path

import numpy as np

from src.cv.io import load_image, save_image


class ImageIoTests(unittest.TestCase):
    def test_round_trip_supports_unicode_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pcb_测试.png"
            source = np.full((32, 40, 3), 123, dtype=np.uint8)
            save_image(path, source)
            loaded = load_image(path)
            self.assertEqual(loaded.shape, source.shape)

    def test_corrupt_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.png"
            path.write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                load_image(path)
