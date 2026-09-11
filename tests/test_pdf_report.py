import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pymupdf

from backend.app.services.pdf_report import (
    ReportDefect,
    ReportGenerationError,
    ReportInspection,
    generate_inspection_report,
    payload_from_record,
)


def image(path: Path):
    board = np.full((360, 640, 3), (35, 85, 68), dtype=np.uint8)
    cv2.line(board, (35, 80), (600, 80), (70, 180, 210), 5)
    cv2.rectangle(board, (240, 140), (330, 195), (220, 220, 215), -1)
    cv2.rectangle(board, (230, 130), (340, 205), (0, 120, 255), 3)
    cv2.putText(board, "major", (230, 120), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 120, 255), 2)
    cv2.imwrite(str(path), board)


def payload(image_path: Path, defects=()):
    return ReportInspection(
        inspection_id="12345678-1234-5678-1234-567812345678", status="PASS WITH WARNING",
        created_at=datetime(2026, 9, 10, 19, 30, tzinfo=UTC),
        model_version="sha256:abc123def456", annotated_image_path=image_path,
        reference_used=True, defects=tuple(defects),
        severity_counts={"critical": 0, "major": 1, "minor": 1},
        alignment_quality={"success": True, "inlier_ratio": .84, "overlap_ratio": .97,
                           "median_reprojection_error": .68},
    )


class PdfReportTests(unittest.TestCase):
    def test_report_contains_required_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); annotated = root / "annotated.png"; image(annotated)
            defects = [
                ReportDefect("misaligned_component", "major", None, "reference_component_contour",
                             {"x_min": 230, "y_min": 130, "x_max": 340, "y_max": 205}),
                ReportDefect("spur", "minor", .82, "yolo_defect",
                             {"x_min": 30, "y_min": 70, "x_max": 75, "y_max": 90}),
            ]
            output = generate_inspection_report(payload(annotated, defects), root / "report.pdf")
            with pymupdf.open(output) as document:
                text = "\n".join(page.get_text() for page in document)
                self.assertTrue(output.read_bytes().startswith(b"%PDF"))
                self.assertIn("PASS WITH WARNING", text)
                self.assertIn("Misaligned Component", text)
                self.assertIn("Heuristic", text)
                self.assertIn("not an industrial certification", text.lower())

    def test_long_defect_log_paginates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); annotated = root / "annotated.png"; image(annotated)
            defects = [ReportDefect("spur", "minor", .5, "yolo_defect",
                      {"x_min": i, "y_min": i, "x_max": i + 10, "y_max": i + 8}) for i in range(55)]
            output = generate_inspection_report(payload(annotated, defects), root / "long.pdf")
            with pymupdf.open(output) as document:
                self.assertGreaterEqual(document.page_count, 2)
                self.assertTrue(all("Academic/research prototype" in page.get_text() for page in document))

    def test_missing_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ReportGenerationError):
            generate_inspection_report(payload(Path(directory) / "missing.png"), Path(directory) / "x.pdf")

    def test_record_adapter_preserves_null_confidence(self):
        record = SimpleNamespace(
            id="abc", status="PASS", created_at=datetime.now(UTC), model_version="test",
            annotated_image_path="annotated.png", summary={"reference_comparison": False, "severity_counts": {}},
            alignment_quality=None,
            defects=[SimpleNamespace(defect_type="spur", severity="minor", confidence=None,
                                     source="rule", bbox={"x_min": 1, "y_min": 2, "x_max": 3, "y_max": 4}, details=None)],
        )
        converted = payload_from_record(record)
        self.assertIsNone(converted.defects[0].confidence)
