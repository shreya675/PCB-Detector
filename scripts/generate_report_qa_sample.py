"""Generate an explicitly synthetic report used only for visual QA."""
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import cv2
import numpy as np

from backend.app.services.pdf_report import (
    ReportDefect,
    ReportInspection,
    generate_inspection_report,
)

root = ROOT / "reports" / "generated" / "qa"
root.mkdir(parents=True, exist_ok=True)
annotated = root / "synthetic-annotated.png"
board = np.full((480, 840, 3), (34, 77, 64), dtype=np.uint8)
for y in (90, 235, 385): cv2.line(board, (40, y), (800, y), (74, 175, 205), 6)
for x in (150, 410, 690): cv2.line(board, (x, 35), (x, 445), (74, 175, 205), 5)
for x, y, w, h in ((90,70,100,45),(330,210,120,52),(620,360,115,46)):
    cv2.rectangle(board,(x,y),(x+w,y+h),(210,210,205),-1)
cv2.rectangle(board,(315,195),(465,277),(0,150,255),4)
cv2.putText(board,"misaligned component",(315,184),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,150,255),2)
cv2.imwrite(str(annotated), board)
defects = (
    ReportDefect("misaligned_component", "major", None, "reference_component_contour", {"x_min":315,"y_min":195,"x_max":465,"y_max":277}),
    ReportDefect("spur", "minor", .823, "yolo_defect", {"x_min":75,"y_min":78,"x_max":115,"y_max":106}),
    ReportDefect("spurious_copper_candidate", "minor", None, "test_minus_reference_connectivity", {"x_min":570,"y_min":330,"x_max":610,"y_max":372}),
)
payload = ReportInspection(
    "synthetic-qa-2026", "PASS WITH WARNING", datetime(2026,9,10,19,30,tzinfo=UTC),
    "qa-only:no-production-model", annotated, True, defects,
    {"critical":0,"major":1,"minor":2},
    {"success":True,"inlier_ratio":.844,"overlap_ratio":.972,"median_reprojection_error":.68},
)
from dataclasses import replace

payload = replace(payload, coverage_warning="Only overlapping board areas were compared. Synthetic layout fixture; not a real inspection.")
generate_inspection_report(payload, root / "synthetic-report.pdf")
print(root / "synthetic-report.pdf")
