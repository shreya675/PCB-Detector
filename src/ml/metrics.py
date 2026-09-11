from __future__ import annotations

from collections.abc import Mapping
from numbers import Real
from typing import Any


def extract_numeric_metrics(metrics: Any) -> dict[str, float]:
    """Extract only values actually returned by Ultralytics; never synthesize metrics."""
    candidates: Any = getattr(metrics, "results_dict", metrics)
    if not isinstance(candidates, Mapping):
        return {}
    observed: dict[str, float] = {}
    for key, value in candidates.items():
        if isinstance(value, Real) and not isinstance(value, bool):
            observed[str(key)] = float(value)
    return observed
