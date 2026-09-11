from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.cv.alignment import align_to_reference
from src.cv.io import load_image, save_image

from .comparison import ComparisonConfig, compare_components
from .detectors import ContourComponentDetector, YoloComponentDetector
from .serialization import comparison_dict
from .visualization import render_comparison


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare components on a test PCB with a reference")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/component-comparison"))
    parser.add_argument("--detector", choices=("contour", "yolo"), default="contour")
    parser.add_argument("--component-weights", type=Path)
    parser.add_argument("--maximum-center-distance", type=float, default=45.0)
    parser.add_argument("--misplaced-center-distance", type=float, default=10.0)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    reference, test = load_image(args.reference), load_image(args.test)
    alignment = align_to_reference(reference, test)
    if not alignment.success:
        raise SystemExit(f"Registration failed; component comparison skipped: {alignment.reason}")
    if args.detector == "yolo":
        if args.component_weights is None:
            raise SystemExit("--component-weights is required for the YOLO component detector")
        detector = YoloComponentDetector(str(args.component_weights))
    else:
        detector = ContourComponentDetector()
    reference_components = detector.detect(reference)
    observed_components = detector.detect(alignment.aligned_image)
    comparison = compare_components(
        reference_components, observed_components,
        ComparisonConfig(maximum_center_distance=args.maximum_center_distance,
                         misplaced_center_distance=args.misplaced_center_distance),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    expected_image, observed_image = render_comparison(reference, alignment.aligned_image, comparison)
    save_image(args.output / "reference_components.png", expected_image)
    save_image(args.output / "test_components.png", observed_image)
    payload = {
        "reference": str(args.reference), "test": str(args.test),
        "detector": args.detector, "alignment": alignment.quality_dict(),
        "comparison": comparison_dict(comparison),
    }
    (args.output / "component_comparison.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(comparison.summary(), indent=2))


if __name__ == "__main__":
    main()
