# PCB AOI — automated optical inspection for printed circuit boards

Detects copper-pattern defects on PCB images with a YOLO11 detector, optionally compares the board
against a defect-free reference, assigns a severity to each finding and produces an annotated image,
a PDF report and a dashboard history.

**Live demo:** https://pcb-aoi-723755393271.us-central1.run.app (first load takes ~30 s while the
container starts; sample images are in `data/processed/deeppcb-official/images/test` after dataset
preparation, or any DeepPCB image works).

## Results

Model: YOLO11m trained on the [DeepPCB](https://github.com/tangsanli5201/DeepPCB) benchmark using the
official trainval/test lists (900 train / 100 val / 500 test images, 1024 px). All numbers are on the
500 held-out test images.

| Setting | Precision | Recall |
|---|---|---|
| Model only (conf 0.25, IoU 0.33) | 93.2% | 94.3% |
| Model + post-processing (as deployed) | **95.8%** | **94.0%** |
| Defect-level (any class) | 96.3% | 94.5% |
| Ultralytics val (conf 0.001): mAP@0.5 / mAP@0.5:0.95 | 97.8% / 74.1% | — |

Post-processing is class-agnostic NMS (IoU 0.2) plus a 1.15× box expansion; it removes 40% of false
positives (214 → 129) at almost no cost in recall. Per-class numbers, training recipe and known
limitations are in [`models/model_card.json`](models/model_card.json) and on the dashboard's
Model performance page. The error analysis behind these numbers is produced by
`scripts/analyze_errors.py`.

## How it works

```text
PCB image
  → validation, CLAHE preprocessing
  → optional ORB + RANSAC registration against a reference image
  → YOLO11 defect detection + post-processing
  → reference comparison: component placement and trace-difference candidates
  → rule-based severity (critical / major / minor)
  → PASS / PASS WITH WARNING / FAIL
  → annotated image, PDF report, inspection history
```

Defect classes: `open_circuit`, `short_circuit`, `spur`, `spurious_copper`, `mouse_bite`, `pin_hole`
(and `missing_hole`, declared for HRIPCB data but absent from DeepPCB). Reference comparison adds
heuristic evidence types (`missing_component`, `bridge_candidate`, …) that are shown with no
confidence score. See [docs/model-classes.md](docs/model-classes.md).

## Stack

FastAPI + SQLAlchemy (SQLite or PostgreSQL) backend, React/Vite/TypeScript dashboard, Ultralytics
YOLO11, OpenCV, ReportLab for PDFs, Docker, GitHub Actions CI, Google Cloud Run.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Database and model readiness |
| GET | `/api/model` | Loaded checkpoint, thresholds and evaluation record |
| POST | `/api/inspect` | Inspect a test image with an optional reference image |
| GET | `/api/inspections` | Paginated history |
| GET | `/api/inspections/{id}` | Inspection details |
| GET | `/api/inspections/{id}/image/{kind}` | Test / reference / annotated image |
| GET | `/api/inspections/{id}/report` | PDF report |

## Run locally

Requirements: Python 3.11+, Node 22+.

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[dev,ml]"
cp .env.example .env
alembic upgrade head
uvicorn backend.app.main:app --reload                 # API on :8000

cd frontend && npm install && npm run dev             # dashboard on :5173
```

Place the weights at `models/weights/yolo11m_official_v4.pt` (download from
[Hugging Face](https://huggingface.co/shreya246/pcb-yolo11m)). Without weights the API returns 503
for inspections.

With Docker: `docker compose up --build` starts PostgreSQL, the API and an nginx-served dashboard on
`http://localhost:8080`.

## Train and evaluate

```bash
python scripts/download_deeppcb.py --accept-research-only            # fetch the dataset
python -m src.datasets.cli deeppcb --source data/raw/DeepPCB/PCBData --output data/processed/deeppcb-official --official-split data/raw/DeepPCB/PCBData
python -m src.ml.cli train    --config ml/configs/yolo_baseline.yaml
python -m src.ml.cli evaluate --config ml/configs/yolo_eval_official.yaml --weights models/weights/yolo11m_official_v4.pt
python scripts/analyze_errors.py --predictions <run>/predictions.json --dataset data/processed/deeppcb-official --split test --postprocess --iou 0.33
```

Details: [docs/datasets.md](docs/datasets.md), [docs/model-training.md](docs/model-training.md).

## Tests

```bash
make check                                    # ruff, compile check, pytest
cd frontend && npm run typecheck && npm run build
```

## Deploy

The root `Dockerfile` builds the dashboard and API into one image. See
[docs/deployment-cloud-run.md](docs/deployment-cloud-run.md) for the Cloud Run setup and
[docs/deployment.md](docs/deployment.md) for Docker Compose.

## Documentation

[Architecture](docs/architecture.md) · [Datasets](docs/datasets.md) · [Model training](docs/model-training.md) ·
[Model classes](docs/model-classes.md) · [Image registration](docs/image-registration.md) ·
[Component comparison](docs/component-comparison.md) · [Trace analysis](docs/advanced-trace-analysis.md) ·
[Backend API](docs/backend-api.md) · [Dashboard](docs/frontend-dashboard.md) · [PDF reports](docs/pdf-reports.md) ·
[Testing](docs/testing.md) · [Security](SECURITY.md)

## License

MIT for the code in this repository. DeepPCB and other datasets remain under their own terms.
