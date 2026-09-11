import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

import cv2
import numpy as np

from src.ml.config import YoloExperimentConfig
from src.ml.training import train_baseline


class FakeResult:
    results_dict: ClassVar[dict] = {"metrics/mAP50(B)": 0.5, "non_numeric": "ignored"}
    def __init__(self, save_dir): self.save_dir = save_dir


class FakeModel:
    def __init__(self, save_dir): self.save_dir, self.kwargs = save_dir, None
    def train(self, **kwargs):
        self.kwargs = kwargs
        weights = self.save_dir / "weights" / "best.pt"
        weights.parent.mkdir(parents=True)
        weights.write_bytes(b"test weights")
        return FakeResult(self.save_dir)


class TrainingTests(unittest.TestCase):
    def test_training_passes_reproducible_settings_and_records_observed_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in ("train", "val"):
                (root / "images" / split).mkdir(parents=True)
                (root / "labels" / split).mkdir(parents=True)
                cv2.imwrite(str(root / "images" / split / "a.jpg"), np.zeros((32, 32, 3), dtype=np.uint8))
                (root / "labels" / split / "a.txt").write_text("")
            names = ["open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole"]
            dataset = root / "dataset.yaml"
            dataset.write_text("path: .\ntrain: images/train\nval: images/val\nnames:\n" +
                               "\n".join(f"  {i}: {n}" for i, n in enumerate(names)) + "\n")
            run = root / "run"
            fake = FakeModel(run)
            config = YoloExperimentConfig(data=str(dataset), project=str(root), name="run", epochs=2, seed=7)
            old = Path.cwd()
            try:
                import os
                os.chdir(root)
                metadata = train_baseline(config, model_factory=lambda _: fake)
            finally:
                os.chdir(old)
            self.assertEqual(fake.kwargs["seed"], 7)
            self.assertTrue(fake.kwargs["deterministic"])
            self.assertEqual(metadata["metrics"], {"metrics/mAP50(B)": 0.5})
            self.assertTrue((run / "run_metadata.json").is_file())
            self.assertTrue(metadata["weights"]["model_version"].startswith("sha256:"))
