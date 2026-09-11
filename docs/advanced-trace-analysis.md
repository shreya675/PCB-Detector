# Phase 6 — Advanced trace-analysis candidates

## Scope and claims

This phase adds deterministic visual evidence for possible trace discontinuities, copper bridges, and spurious copper. Outputs deliberately use the suffix `_candidate`: they are not electrical continuity measurements, solder-joint classifications, calibrated probabilities, or industrial pass/fail decisions.

## Pipeline

1. Require successful Phase 4 registration.
2. Segment copper-like pixels independently in the reference and aligned test image.
3. Restrict all operations to the valid registration overlap.
4. Apply a configurable spatial tolerance to suppress one- or two-pixel alignment noise.
5. Skeletonize the reference copper mask.
6. Intersect missing copper with the expected skeleton to produce broken-trace candidates.
7. Label reference copper regions and test whether added copper contacts multiple expected regions.
8. Mark additions contacting multiple regions as bridge candidates; other additions become spurious-copper candidates.
9. Fuse overlapping evidence of the same category without treating heuristic strength as probability.

## CLI

```bash
python -m src.inspection.trace_cli \
  --reference samples/reference.png \
  --test samples/test.png \
  --output reports/trace-analysis
```

Useful capture-specific controls:

```bash
--threshold 140
--copper-is-dark
--minimum-area 20
```

Outputs:

```text
reference_copper.png
test_copper.png
reference_skeleton.png
missing_copper.png
added_copper.png
trace_candidates.png
trace_analysis.json
```

## Calibration guidance

Inspect masks before interpreting candidates. Copper brightness, solder mask color, illumination, exposure, and camera modality can reverse or invalidate a global threshold. Tune on a held-out calibration set and record the settings. Do not tune against the final test set.

## Limitations

- Pixel segmentation does not prove electrical continuity.
- A visible bridge is not necessarily a solder bridge.
- Shadows, glare, contamination, print, and registration residuals can cause false candidates.
- Hidden-layer, via-barrel, underside, and subsurface faults are not observable from one surface image.
- Cold solder, tombstoning, and polarity errors require suitable labeled data and/or dedicated geometry rules.
- Final severity and PASS/WARNING/FAIL policy are implemented in the backend phase using configurable rules.
