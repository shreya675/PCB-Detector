"""Dependency-light Phase 8 contract tests; frontend build runs when npm dependencies are installed."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
suite = unittest.TestLoader().loadTestsFromName("tests.test_frontend_contract")
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
