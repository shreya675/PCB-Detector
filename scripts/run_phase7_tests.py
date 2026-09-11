"""Phase 7 tests. API tests run automatically when their dependencies are installed."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

suite = unittest.TestLoader().loadTestsFromNames([
    "tests.test_severity", "tests.test_inspection_engine", "tests.test_storage", "tests.test_api_phase7",
])
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
