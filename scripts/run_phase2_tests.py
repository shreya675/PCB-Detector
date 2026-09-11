"""Dependency-light Phase 2 test runner; the same unittest tests are Pytest-compatible."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

suite = unittest.TestLoader().loadTestsFromNames([
    "tests.test_dataset_schema",
    "tests.test_dataset_converters",
    "tests.test_dataset_pipeline",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
