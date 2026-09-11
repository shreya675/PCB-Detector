"""Component detection and reference-to-test PCB comparison."""

from .comparison import ComparisonConfig, ComparisonResult, compare_components
from .components import BoundingBox, ComponentDetection, ComponentDetector
from .detectors import ContourComponentDetector, ContourDetectorConfig, YoloComponentDetector

__all__ = [
    "BoundingBox",
    "ComparisonConfig",
    "ComparisonResult",
    "ComponentDetection",
    "ComponentDetector",
    "ContourComponentDetector",
    "ContourDetectorConfig",
    "TraceAnalysisConfig",
    "TraceAnalysisResult",
    "TraceCandidate",
    "YoloComponentDetector",
    "analyze_trace_differences",
    "compare_components",
]

from .trace_analysis import (
    TraceAnalysisConfig,
    TraceAnalysisResult,
    TraceCandidate,
    analyze_trace_differences,
)
