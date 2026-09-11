from unittest.mock import patch

import cv2
import numpy as np

from backend.app.services.inspection_engine import InspectionEngine
from backend.app.services.severity import SeverityPolicy
from src.cv.alignment import AlignmentResult
from src.inspection.trace_analysis import skeletonize
from tests.test_inspection_engine import FakeDetector


def test_detector_receives_aligned_image():
    test = np.zeros((80, 100, 3), dtype=np.uint8)
    aligned = np.full((120, 160, 3), 130, dtype=np.uint8)
    mask = np.full(aligned.shape[:2], 255, dtype=np.uint8)
    alignment = AlignmentResult(True, aligned, np.eye(3), mask, 20, 20, 20, 20, 20, 1., 0., 1.)
    detector = FakeDetector()
    engine = InspectionEngine(detector, SeverityPolicy({}))
    with patch('backend.app.services.inspection_engine.align_to_reference', return_value=alignment), \
         patch.object(engine, '_reference_findings', return_value=[]), \
         patch.object(detector, 'detect', return_value=()) as detect:
        result = engine.inspect(test, aligned)
    assert detect.call_args.args[0] is aligned
    assert result.annotated_image.shape == aligned.shape
    assert result.summary['coordinate_frame'] == 'reference'


def test_disabled_reference_is_not_reported_as_used():
    image = np.zeros((80, 100, 3), dtype=np.uint8)
    result = InspectionEngine(FakeDetector(), SeverityPolicy({}), False).inspect(image, image)
    assert result.summary['reference_comparison'] is False


def test_partial_coverage_never_returns_unqualified_pass():
    image = np.zeros((80, 100, 3), dtype=np.uint8)
    mask = np.full((80, 100), 255, dtype=np.uint8)
    mask[:, :20] = 0
    alignment = AlignmentResult(True, image, np.eye(3), mask, 20, 20, 20, 20, 20, 1., 0., .8)
    engine = InspectionEngine(FakeDetector(), SeverityPolicy({}))
    with patch('backend.app.services.inspection_engine.align_to_reference', return_value=alignment), \
         patch.object(engine, '_reference_findings', return_value=[]):
        result = engine.inspect(image, image)
    assert result.status == 'PASS WITH WARNING'
    assert result.summary['coverage_warning']


def test_uncovered_component_is_not_reported_missing():
    reference = np.full((200, 200, 3), 255, dtype=np.uint8)
    cv2.rectangle(reference, (20, 40), (40, 60), (0, 0, 0), -1)
    observed = reference.copy()
    observed[:, :70] = 0
    mask = np.full((200, 200), 255, dtype=np.uint8)
    mask[:, :70] = 0
    findings = InspectionEngine(FakeDetector(), SeverityPolicy({}))._reference_findings(reference, observed, mask)
    assert not any(item.defect_type == 'missing_component' for item in findings)


def test_solid_foreground_skeleton_terminates():
    skeleton = skeletonize(np.full((32, 32), 255, dtype=np.uint8))
    assert skeleton.shape == (32, 32)
    assert np.count_nonzero(skeleton) > 0
