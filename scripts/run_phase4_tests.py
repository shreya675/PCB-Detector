"""Dependency-light Phase 4 test runner; these unittest cases are also Pytest-compatible."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

suite = unittest.TestLoader().loadTestsFromNames([
    "tests.test_cv_preprocessing", "tests.test_cv_alignment",
    "tests.test_cv_difference", "tests.test_cv_io",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
