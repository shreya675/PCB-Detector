import tempfile
import unittest
from pathlib import Path

from src.datasets.converters import parse_deeppcb_annotation, parse_voc_annotation


class DatasetConverterTests(unittest.TestCase):
    def test_deeppcb_class_order_is_remapped(self):
        with tempfile.TemporaryDirectory() as directory:
            label = Path(directory) / "sample.txt"
            label.write_text("1,2,11,22,3\n20,30,40,50,6\n", encoding="utf-8")
            boxes = parse_deeppcb_annotation(label)
            self.assertEqual([box.class_id for box in boxes], [4, 6])

    def test_invalid_deeppcb_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            label = Path(directory) / "bad.txt"
            label.write_text("1,2,3\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_deeppcb_annotation(label)

    def test_voc_alias_is_converted(self):
        xml = """<annotation><filename>a.jpg</filename><object><name>spurious copper</name><bndbox><xmin>1</xmin><ymin>2</ymin><xmax>9</xmax><ymax>10</ymax></bndbox></object></annotation>"""
        with tempfile.TemporaryDirectory() as directory:
            annotation = Path(directory) / "a.xml"
            annotation.write_text(xml, encoding="utf-8")
            filename, boxes = parse_voc_annotation(annotation)
            self.assertEqual(filename, "a.jpg")
            self.assertEqual(boxes[0].class_id, 3)
