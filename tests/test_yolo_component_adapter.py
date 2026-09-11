import unittest

import numpy as np

from src.inspection.detectors import YoloComponentDetector


class FakeTensor:
    def __init__(self, value): self.value = value
    def cpu(self): return self
    def tolist(self): return self.value


class FakeModel:
    def predict(self, **kwargs):
        boxes = type("Boxes", (), {
            "xyxy": FakeTensor([[1, 2, 11, 12]]), "conf": FakeTensor([0.8]), "cls": FakeTensor([0]),
        })()
        return [type("Result", (), {"boxes": boxes, "names": {0: "resistor"}})()]


class YoloComponentAdapterTests(unittest.TestCase):
    def test_converts_model_output(self):
        detector = YoloComponentDetector("fake.pt", model_factory=lambda _: FakeModel())
        result = detector.detect(np.zeros((32, 32, 3), dtype=np.uint8))
        self.assertEqual(result[0].label, "resistor")
        self.assertEqual(result[0].confidence, 0.8)
