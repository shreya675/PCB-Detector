from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .comparison import ComparisonResult
from .components import ComponentDetection


def detection_dict(detection: ComponentDetection) -> dict[str, Any]:
    return asdict(detection)


def comparison_dict(result: ComparisonResult) -> dict[str, Any]:
    return {
        "summary": result.summary(),
        "matches": [asdict(match) for match in result.matches],
        "missing": [detection_dict(item) for item in result.missing],
        "unexpected": [detection_dict(item) for item in result.unexpected],
        "method_note": "Contour detections are heuristic candidates unless a trained component model is supplied.",
    }
