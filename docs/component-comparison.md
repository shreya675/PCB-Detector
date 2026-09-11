# Phase 5 — Component detection and reference comparison

## Design

The component layer accepts any detector implementing `detect(image) -> tuple[ComponentDetection, ...]`. Two adapters are provided:

- `ContourComponentDetector`: a dataset-free classical baseline for dark, component-like connected regions. It emits `generic_component` candidates and no confidence value.
- `YoloComponentDetector`: an adapter for separately trained component-detection weights. No component dataset, weights, accuracy, or confidence claims are bundled.

## Comparison

The test board is first aligned into reference coordinates using Phase 4. Comparison is skipped if registration quality fails. One-to-one matching then combines:

- center displacement,
- logarithmic area ratio,
- orientation difference,
- compatible component labels when labels are available.

Candidate pairs are sorted by total cost and greedily assigned without reusing either detection. Results are:

- `matched`: within placement, area, and orientation tolerances;
- `misplaced`: matchable but outside one or more placement tolerances;
- `missing`: expected reference component has no acceptable observed match;
- `unexpected`: observed test component has no acceptable reference match.

Thresholds are configuration, not certified manufacturing tolerances.

## CLI

Classical proposal baseline:

```bash
python -m src.inspection.cli \
  --reference samples/reference.png \
  --test samples/test.png \
  --detector contour \
  --output reports/component-comparison
```

With future component weights:

```bash
python -m src.inspection.cli \
  --reference samples/reference.png \
  --test samples/test.png \
  --detector yolo \
  --component-weights models/weights/components.pt
```

The command writes `component_comparison.json`, `reference_components.png`, and `test_components.png`.

## Important limitations

- A contour proposal is not semantic component recognition.
- Silkscreen, vias, traces, shadows, and dark substrate regions may become false candidates.
- Reliable missing-component results require repeatable imaging and a detector trained for the relevant component families.
- Polarity, tombstoning, solder quality, and electrical continuity are not inferred in this phase.
- Comparison is suppressed when registration fails, preventing alignment errors from being presented as component defects.
