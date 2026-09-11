# Phase 3 — YOLO baseline

## Scope

This phase supplies reproducible baseline tooling, not pretrained project weights or claimed performance. Training requires a prepared dataset from Phase 2 and the optional ML dependencies.

Ultralytics exposes Python `train`, `val`, and `predict` modes. The baseline fixes the seed, requests deterministic execution, saves plots/checkpoints, and stores only numeric metrics returned by the library.

## Workflow

```bash
pip install -e ".[ml,dev]"
python -m src.ml.cli preflight --config ml/configs/yolo_baseline.yaml
python -m src.ml.cli train --config ml/configs/yolo_baseline.yaml
python -m src.ml.cli evaluate --config ml/configs/yolo_baseline.yaml \
  --weights reports/training/deeppcb-yolo11n-baseline/weights/best.pt
python -m src.ml.cli predict \
  --weights reports/training/deeppcb-yolo11n-baseline/weights/best.pt \
  --source samples/pcb.jpg --output reports/predictions
```

## Reproducibility records

Training produces a `run_metadata.json` beside the run and appends a JSON line to `models/registry.jsonl`. Evaluation writes `metrics.json`. Records include resolved configuration, observed dataset counts, environment versions, UTC timestamp, and the best-weight SHA-256 when available. A model version has the form `sha256:<12 hex characters>`.

## Metric policy

- No values are created when Ultralytics returns no metrics.
- No sample or placeholder values appear in the model registry.
- Do not compare runs unless they use the same split, class order, image size, and evaluation settings.
- Preserve raw Ultralytics run artifacts for auditability.

## Expected limitations

DeepPCB and HRIPCB contain aligned, cropped, and/or synthesized content. A strong benchmark score does not prove robustness to production cameras, illumination, contamination, novel board layouts, or unseen defect morphology.

## Evaluation split

`evaluation_split` defaults to `test`; use `val` explicitly for development checks.
The chosen split is recorded in evaluation metadata. Evaluation metrics are saved
in the directory returned by Ultralytics, including suffixed repeat-run directories.
Never report training or validation scores as held-out test performance.
