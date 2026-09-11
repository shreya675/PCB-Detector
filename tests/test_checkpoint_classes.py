from types import SimpleNamespace

import numpy as np
import pytest

from backend.app.services.detector import ModelUnavailableError, UltralyticsDefectDetector
from src.ml.classes import resolve_model_classes
from tests.test_ml_inference import FakeTensor


def test_reordered_checkpoint_labels_are_respected(tmp_path):
    weights = tmp_path / 'unit-test.pt'
    weights.write_bytes(b'test double, not model weights')
    boxes = SimpleNamespace(xyxy=FakeTensor([[2, 3, 10, 12]]), conf=FakeTensor([.8]), cls=FakeTensor([0]))
    model = SimpleNamespace(names={0: 'mouse_bite', 1: 'open'}, predict=lambda **kwargs: [SimpleNamespace(boxes=boxes)])
    detector = UltralyticsDefectDetector(weights, model_factory=lambda _: model)
    assert detector.detect(np.zeros((32, 32, 3), np.uint8))[0].defect_type == 'mouse_bite'


def test_generic_coco_checkpoint_is_rejected(tmp_path):
    weights = tmp_path / 'unit-test.pt'
    weights.write_bytes(b'test double')
    detector = UltralyticsDefectDetector(weights, model_factory=lambda _: SimpleNamespace(names={0: 'person'}))
    with pytest.raises(ModelUnavailableError):
        detector.detect(np.zeros((32, 32, 3), np.uint8))


def test_pin_hole_and_missing_hole_are_distinct():
    assert resolve_model_classes(['pin-hole', 'missing hole']) == {0: 'pin_hole', 1: 'missing_hole'}
