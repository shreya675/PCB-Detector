"""Dependency-light Phase 5 test runner; these unittest cases are Pytest-compatible."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

suite = unittest.TestLoader().loadTestsFromNames([
    "tests.test_component_detector", "tests.test_component_comparison",
    "tests.test_yolo_component_adapter", "tests.test_component_serialization",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
