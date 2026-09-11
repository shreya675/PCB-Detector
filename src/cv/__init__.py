"""OpenCV preprocessing, PCB registration, and visible-difference analysis."""

from .alignment import AlignmentConfig, AlignmentResult, align_to_reference
from .difference import DifferenceConfig, DifferenceRegion, DifferenceResult, compute_difference
from .preprocessing import PreprocessConfig, preprocess_for_features, validate_image

__all__ = [
    "AlignmentConfig",
    "AlignmentResult",
    "DifferenceConfig",
    "DifferenceRegion",
    "DifferenceResult",
    "PreprocessConfig",
    "align_to_reference",
    "compute_difference",
    "preprocess_for_features",
    "validate_image",
]
