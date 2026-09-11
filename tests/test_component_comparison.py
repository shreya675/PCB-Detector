import unittest

from src.inspection.comparison import ComparisonConfig, compare_components
from src.inspection.components import BoundingBox, ComponentDetection


def component(identifier: str, x: float, y: float, label: str = "resistor", angle: float = 0) -> ComponentDetection:
    return ComponentDetection(identifier, label, BoundingBox(x, y, x + 20, y + 10), angle)


class ComponentComparisonTests(unittest.TestCase):
    def test_exact_components_match(self):
        result = compare_components((component("r1", 10, 10),), (component("o1", 11, 11),))
        self.assertEqual(result.summary()["matched"], 1)
        self.assertEqual(result.summary()["missing"], 0)

    def test_missing_component_is_reported(self):
        result = compare_components((component("r1", 10, 10), component("r2", 100, 100)),
                                    (component("o1", 11, 11),))
        self.assertEqual([item.detection_id for item in result.missing], ["r2"])

    def test_shifted_component_is_misplaced(self):
        config = ComparisonConfig(maximum_center_distance=40, misplaced_center_distance=5)
        result = compare_components((component("r1", 10, 10),), (component("o1", 22, 10),), config)
        self.assertEqual(result.summary()["misplaced"], 1)

    def test_wrong_known_label_is_not_matched(self):
        result = compare_components((component("r1", 10, 10, "resistor"),),
                                    (component("o1", 10, 10, "capacitor"),))
        self.assertEqual(result.summary()["missing"], 1)
        self.assertEqual(result.summary()["unexpected"], 1)

    def test_one_observation_cannot_match_two_references(self):
        result = compare_components((component("r1", 10, 10), component("r2", 12, 10)),
                                    (component("o1", 11, 10),))
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(len(result.missing), 1)
