import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.ml.preflight import validate_yolo_dataset


class PreflightTests(unittest.TestCase):
    def make_dataset(self, root: Path) -> Path:
        names = ["open_circuit", "short_circuit", "spur", "spurious_copper", "mouse_bite", "missing_hole", "pin_hole"]
        for split in ("train", "val"):
            (root / "images" / split).mkdir(parents=True)
            (root / "labels" / split).mkdir(parents=True)
            cv2.imwrite(str(root / "images" / split / f"{split}.jpg"), np.zeros((32, 32, 3), dtype=np.uint8))
            (root / "labels" / split / f"{split}.txt").write_text("0 0.5 0.5 0.2 0.2\n")
        yaml = root / "dataset.yaml"
        yaml.write_text("path: .\ntrain: images/train\nval: images/val\nnames:\n" +
                        "\n".join(f"  {i}: {name}" for i, name in enumerate(names)) + "\n")
        return yaml

    def test_valid_dataset_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = validate_yolo_dataset(self.make_dataset(Path(directory)))
            self.assertEqual(report.split_counts, {"train": 1, "val": 1})

    def test_missing_label_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            yaml = self.make_dataset(root)
            (root / "labels" / "val" / "val.txt").unlink()
            with self.assertRaises(ValueError):
                validate_yolo_dataset(yaml)

    def test_nonfinite_annotation_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dataset = self.make_dataset(root)
            (root / "labels" / "val" / "val.txt").write_text("0 nan 0.5 0.2 0.2\n")
            with self.assertRaises(ValueError):
                validate_yolo_dataset(dataset)
