import unittest

from src.ml.metrics import extract_numeric_metrics


class MetricsTests(unittest.TestCase):
    def test_extracts_only_observed_numeric_values(self):
        fake = type("Metrics", (), {"results_dict": {"mAP50": 0.75, "label": "x", "flag": True}})()
        self.assertEqual(extract_numeric_metrics(fake), {"mAP50": 0.75})

    def test_does_not_invent_metrics(self):
        self.assertEqual(extract_numeric_metrics(object()), {})
