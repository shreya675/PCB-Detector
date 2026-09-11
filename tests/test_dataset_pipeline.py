import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.datasets.io import read_image_size
from src.datasets.prepare import prepare_deeppcb, prepare_hripcb, validate_prepared_dataset


def write_image(path: Path, width: int = 64, height: int = 48) -> None:
    image = np.full((height, width, 3), 180, dtype=np.uint8)
    ok, encoded = cv2.imencode(path.suffix, image)
    assert ok
    encoded.tofile(path)


class DatasetPipelineTests(unittest.TestCase):
    def test_official_deeppcb_sibling_annotation_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source"
            images = source / "group20085" / "20085"
            labels = source / "group20085" / "20085_not"
            images.mkdir(parents=True)
            labels.mkdir()
            write_image(images / "20085000_test.jpg")
            write_image(images / "20085000_temp.jpg")
            (labels / "20085000.txt").write_text("5 6 20 22 6\n")
            records = prepare_deeppcb(source, Path(directory) / "output")
            self.assertEqual(records[0].boxes[0].class_id, 6)

    def test_deeppcb_pair_is_prepared_with_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source", root / "output"
            source.mkdir()
            write_image(source / "00010001_test.jpg")
            write_image(source / "00010001_temp.jpg")
            (source / "00010001.txt").write_text("5,6,20,22,1\n", encoding="utf-8")
            records = prepare_deeppcb(source, output)
            self.assertEqual(len(records), 1)
            self.assertTrue((output / records[0].image).is_file())
            self.assertTrue((output / records[0].reference_image).is_file())
            self.assertEqual(validate_prepared_dataset(output), {"images": 1, "annotations": 1})
            summary = json.loads((output / "summary.json").read_text())
            self.assertEqual(summary["classes"]["open_circuit"], 1)

    def test_incomplete_deeppcb_pair_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            write_image(source / "00010001_test.jpg")
            (source / "00010001.txt").write_text("5,6,20,22,1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                prepare_deeppcb(source, output)

    def test_corrupt_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "corrupt.jpg"
            image.write_bytes(b"not an image")
            with self.assertRaises(ValueError):
                read_image_size(image)

    def test_hripcb_voc_is_prepared(self):
        xml = """<annotation><filename>board01.jpg</filename><object><name>missing hole</name><bndbox><xmin>2</xmin><ymin>3</ymin><xmax>20</xmax><ymax>22</ymax></bndbox></object></annotation>"""
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / "source", Path(directory) / "output"
            source.mkdir()
            write_image(source / "board01.jpg")
            (source / "board01.xml").write_text(xml, encoding="utf-8")
            records = prepare_hripcb(source, output)
            self.assertEqual(records[0].boxes[0].class_id, 5)
            self.assertEqual(validate_prepared_dataset(output)["images"], 1)
