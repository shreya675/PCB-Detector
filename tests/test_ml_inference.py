import unittest

from src.datasets.schema import CLASS_NAMES
from src.ml.inference import parse_result


class FakeTensor:
    def __init__(self, value): self.value = value
    def cpu(self): return self
    def tolist(self): return self.value


class InferenceTests(unittest.TestCase):
    def test_result_is_normalized(self):
        boxes = type("Boxes", (), {
            "xyxy": FakeTensor([[1, 2, 10, 20]]),
            "conf": FakeTensor([0.875]),
            "cls": FakeTensor([4]),
        })()
        result = type("Result", (), {"names": dict(enumerate(CLASS_NAMES)), "boxes": boxes, "path": "board.jpg"})()
        prediction = parse_result(result)
        self.assertEqual(prediction.detections[0].class_name, "mouse_bite")
        self.assertEqual(prediction.detections[0].confidence, 0.875)

    def test_unknown_class_is_rejected(self):
        boxes = type("Boxes", (), {
            "xyxy": FakeTensor([[1, 2, 10, 20]]),
            "conf": FakeTensor([0.5]),
            "cls": FakeTensor([99]),
        })()
        with self.assertRaises(ValueError):
            parse_result(type("Result", (), {"names": dict(enumerate(CLASS_NAMES)), "boxes": boxes, "path": "x.jpg"})())
