import unittest

from src.datasets.schema import BoundingBox, canonical_class_name
from src.datasets.splitting import assert_no_group_leakage, board_group, stable_split


class DatasetSchemaTests(unittest.TestCase):
    def test_hripcb_defect_variants_stay_in_same_board_group(self):
        self.assertEqual(board_group("01_missing_hole_01"), board_group("01_open_circuit_02"))

    def test_box_converts_to_normalized_yolo(self):
        self.assertEqual(BoundingBox(0, 10, 20, 30, 60).to_yolo(100, 100),
                         "0 0.20000000 0.40000000 0.20000000 0.40000000")

    def test_invalid_box_is_rejected(self):
        with self.assertRaises(ValueError):
            BoundingBox(0, 30, 20, 10, 60).to_yolo(100, 100)

    def test_aliases_are_canonicalized(self):
        self.assertEqual(canonical_class_name("pin-hole"), "pin_hole")
        self.assertEqual(canonical_class_name("Mouse Bite"), "mouse_bite")

    def test_split_is_deterministic(self):
        self.assertEqual(stable_split("board-1"), stable_split("board-1"))

    def test_group_leakage_is_rejected(self):
        with self.assertRaises(ValueError):
            assert_no_group_leakage([("board-1", "train"), ("board-1", "test")])
