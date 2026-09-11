# PCB AOI — AI-Powered Optical Inspection

A portfolio-level **academic/research prototype** for detecting visible PCB defects, comparing a test image with an optional reference board, assigning explainable severity, and publishing annotated results and PDF reports through a FastAPI API and React dashboard.

> **Safety notice:** This is not an industrially certified inspection system, electrical continuity test, or substitute for qualified human inspection. No trained project weights or measured model performance are bundled.

## Pipeline

```text
PCB image
  → validation and CLAHE preprocessing
  → optional ORB/RANSAC registration
  → YOLO defect detection
  → component/reference comparison
  → trace-candidate evidence
  → rule-based severity
  → PASS / PASS WITH WARNING / FAIL
  → annotated image + PDF report + dashboard history
```

## Model output classes

The output taxonomy preserves the requested categories plus DeepPCB pin holes:

1. `open_circuit`
2. `short_circuit`
3. `spur`
4. `spurious_copper`
5. `mouse_bite`
6. `missing_hole`
7. `pin_hole` (DeepPCB-specific; distinct from a missing drilled hole)

The repository contains training/evaluation code but **no trained weights**, so it currently makes no operational model prediction until a real `best.pt` is supplied. Reference comparison can produce six additional heuristic evidence types; these are not model classes or probabilities. See [docs/model-classes.md](docs/model-classes.md).

## Features

- Deterministic DeepPCB/HRIPCB preparation and grouped splits
- Reproducible Ultralytics training, validation, inference, and model registry
- OpenCV preprocessing, registration quality gates, and visual differencing
- Component matching and trace-candidate analysis
- Configurable severity policy and auditable decisions
- FastAPI endpoints with SQLite/PostgreSQL persistence
- Responsive React/Vite engineering dashboard
- A4 PDF reports with provenance and prototype disclaimers
- Alembic schema migration, hardened containers, and CI workflows

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Database and model readiness |
| POST | `/api/inspect` | Inspect test image with optional reference |
| GET | `/api/inspections` | Paginated history |
| GET | `/api/inspections/{id}` | Inspection details |
| GET | `/api/inspections/{id}/image/{kind}` | Test/reference/annotated image |
| GET | `/api/inspections/{id}/report` | Generate or download PDF |

## Local setup

Requirements: Python 3.11+ and Node 22+.

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
alembic upgrade head
cd frontend && npm install && cd ..
```

Install the ML stack only for training/inference:

```bash
pip install -e ".[ml]"
```

Run locally:

```bash
make api       # API: http://localhost:8000
make frontend  # Dashboard: http://localhost:5173
```

Or use PostgreSQL and containers:

```bash
docker compose up --build
# Dashboard: http://localhost:8080
```

## Validation

```bash
make verify
pytest
cd frontend && npm run typecheck && npm run build
```

In limited environments, dependency-backed API tests, Docker builds, or frontend builds may be unavailable. Skips are reported separately and are never counted as passes. Synthetic CV fixtures validate logic, not real-world accuracy.

## Project status

All ten phases have implementation code. Dataset acquisition, real model training, held-out evaluation, and deployment validation remain pending:

- Project scaffold and architecture
- Dataset preparation
- YOLO baseline
- Registration and preprocessing
- Component comparison
- Trace candidate analysis
- API and persistence
- Dashboard
- PDF reports
- Testing, migrations, containers, CI, security, and documentation

## Documentation

- [Architecture](docs/architecture.md)
- [Datasets](docs/datasets.md)
- [Model training](docs/model-training.md)
- [Model classes](docs/model-classes.md)
- [Image registration](docs/image-registration.md)
- [Component comparison](docs/component-comparison.md)
- [Trace analysis](docs/advanced-trace-analysis.md)
- [Backend API](docs/backend-api.md)
- [Dashboard](docs/frontend-dashboard.md)
- [PDF reports](docs/pdf-reports.md)
- [Testing](docs/testing.md)
- [Deployment](docs/deployment.md)
- [Security](SECURITY.md)

Project code is MIT licensed. Dataset and model artifacts remain subject to their original terms.

## Windows (PowerShell)

Run commands from `pcb-aoi-final/pcb-aoi`, the active project in this workspace.
Redundant historical phase snapshots were removed during GitHub preparation.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env  # only when .env does not already exist
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
# In another terminal:
cd frontend
npm ci
npm run dev
```

Install `.[ml]` into the same environment before using real checkpoint weights.
Missing weights return HTTP 503; the application never substitutes fake detections.
DeepPCB does not provide missing-hole examples: prepare suitable HRIPCB data for
that category. Previously prepared data must be regenerated after the taxonomy fix.
Only categories represented in the training data can be evaluated meaningfully.

See [workspace audit](docs/workspace-audit.md) for corrections and validation results.
