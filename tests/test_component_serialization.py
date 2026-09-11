import unittest

from src.inspection.comparison import compare_components
from src.inspection.components import BoundingBox, ComponentDetection
from src.inspection.serialization import comparison_dict


class ComponentSerializationTests(unittest.TestCase):
    def test_summary_is_serializable(self):
        reference = (ComponentDetection("r1", "generic_component", BoundingBox(1, 1, 10, 10)),)
        payload = comparison_dict(compare_components(reference, ()))
        self.assertEqual(payload["summary"]["missing"], 1)
        self.assertIn("heuristic", payload["method_note"])
