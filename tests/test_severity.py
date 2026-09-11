import tempfile
import unittest
from pathlib import Path

from backend.app.services.severity import SeverityPolicy


class SeverityTests(unittest.TestCase):
    def setUp(self):
        self.policy = SeverityPolicy({"short_circuit": "critical", "mouse_bite": "major", "spur": "minor"})

    def test_no_defects_passes(self):
        self.assertEqual(self.policy.decide([])[0], "PASS")

    def test_minor_warns(self):
        self.assertEqual(self.policy.decide(["minor"])[0], "PASS WITH WARNING")

    def test_single_major_warns(self):
        self.assertEqual(self.policy.decide(["major"])[0], "PASS WITH WARNING")

    def test_multiple_major_fail(self):
        self.assertEqual(self.policy.decide(["major", "major"])[0], "FAIL")

    def test_critical_fails(self):
        self.assertEqual(self.policy.decide(["critical"])[0], "FAIL")

    def test_mapping_and_default(self):
        self.assertEqual(self.policy.severity_for("short_circuit"), "critical")
        self.assertEqual(self.policy.severity_for("unknown_candidate"), "minor")

    def test_yaml_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "policy.yaml"
            path.write_text("default_severity: impossible\ndefect_severity: {}\n")
            with self.assertRaises(ValueError):
                SeverityPolicy.from_yaml(path)
