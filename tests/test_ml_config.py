import tempfile
import unittest
from pathlib import Path

from src.ml.config import load_experiment_config


class MlConfigTests(unittest.TestCase):
    def test_loads_valid_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("model: yolo11n.pt\ndata: dataset.yaml\nepochs: 2\n", encoding="utf-8")
            config = load_experiment_config(path)
            self.assertEqual(config.epochs, 2)
            self.assertTrue(config.deterministic)

    def test_rejects_unknown_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("made_up_metric: 0.99\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_experiment_config(path)
