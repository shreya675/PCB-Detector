import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from backend.app.services.storage import InspectionStorage, InvalidUploadError


class StorageTests(unittest.TestCase):
    def test_valid_image_decodes(self):
        image = np.zeros((32, 40, 3), dtype=np.uint8)
        ok, encoded = cv2.imencode(".png", image)
        self.assertTrue(ok)
        with tempfile.TemporaryDirectory() as directory:
            decoded, relative = InspectionStorage(Path(directory)).decode_upload(encoded.tobytes(), "board.png", "test")
            self.assertEqual(decoded.shape, image.shape)
            self.assertEqual(relative.name, "test.png")

    def test_corrupt_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(InvalidUploadError):
            InspectionStorage(Path(directory)).decode_upload(b"corrupt", "board.png", "test")

    def test_oversize_upload_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(InvalidUploadError):
            InspectionStorage(Path(directory), max_upload_mb=0).decode_upload(b"x", "x.png", "test")
