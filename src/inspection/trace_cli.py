from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from src.cv.alignment import align_to_reference
from src.cv.io import load_image, save_image

from .evidence import fuse_trace_evidence
from .trace_analysis import TraceAnalysisConfig, analyze_trace_differences
from .trace_visualization import render_trace_candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze aligned PCB copper/trace differences")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("reports/trace-analysis"))
    parser.add_argument("--threshold", type=int)
    parser.add_argument("--copper-is-dark", action="store_true")
    parser.add_argument("--minimum-area", type=int, default=12)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    reference, test = load_image(args.reference), load_image(args.test)
    alignment = align_to_reference(reference, test)
    if not alignment.success:
        raise SystemExit(f"Registration failed; trace analysis skipped: {alignment.reason}")
    config = TraceAnalysisConfig(
        threshold=args.threshold, copper_is_bright=not args.copper_is_dark,
        minimum_region_area=args.minimum_area,
    )
    result = analyze_trace_differences(reference, alignment.aligned_image, alignment.valid_mask, config)
    evidence = fuse_trace_evidence(result.candidates)
    args.output.mkdir(parents=True, exist_ok=True)
    outputs = {
        "reference_copper.png": result.reference_copper_mask,
        "test_copper.png": result.test_copper_mask,
        "reference_skeleton.png": result.reference_skeleton,
        "missing_copper.png": result.missing_copper_mask,
        "added_copper.png": result.added_copper_mask,
        "trace_candidates.png": render_trace_candidates(alignment.aligned_image, result.candidates),
    }
    for name, image in outputs.items():
        save_image(args.output / name, image)
    payload = {
        "reference": str(args.reference), "test": str(args.test),
        "alignment": alignment.quality_dict(), "configuration": asdict(config),
        "trace_analysis": result.json_dict(),
        "fused_evidence": [asdict(item) for item in evidence],
        "interpretation": "Heuristic visual candidates; not electrical-test results or calibrated probabilities.",
    }
    (args.output / "trace_analysis.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result.summary(), indent=2))


if __name__ == "__main__":
    main()
