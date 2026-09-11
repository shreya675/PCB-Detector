"""Dependency-light Phase 3 test runner; these unittest cases are also Pytest-compatible."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

suite = unittest.TestLoader().loadTestsFromNames([
    "tests.test_ml_config", "tests.test_ml_metrics", "tests.test_ml_preflight",
    "tests.test_ml_training", "tests.test_ml_inference",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
