# Phase 7 — FastAPI backend and persistence

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | API, database, model-configuration health |
| POST | `/api/inspect` | Upload test PCB and optional reference PCB |
| GET | `/api/inspections` | Paginated inspection history |
| GET | `/api/inspections/{id}` | Inspection details and defects |
| GET | `/api/inspections/{id}/image/{kind}` | Serve test, reference, or annotated image |
| GET | `/api/inspections/{id}/report` | Download a Phase 9 PDF when available |

## Inspection behavior

The API validates uploaded bytes with OpenCV, rejects oversize or corrupt files, runs the configured defect detector, optionally performs registration/component/trace comparison, assigns configurable severity, stores artifacts, and commits inspection plus defect rows in one database transaction.

A missing model returns HTTP 503 rather than silently returning PASS. Failed registration returns HTTP 422 and does not create a misleading inspection result.

## Severity policy

Rules live in `backend/app/core/severity.yaml`.

- Any configured critical defect causes `FAIL`.
- Two or more major defects cause `FAIL` by default.
- One major defect causes `PASS WITH WARNING` by default.
- One or more minor defects causes `PASS WITH WARNING`.
- No findings causes `PASS`.

Heuristic reference candidates have no fabricated confidence value. Their severity is configurable separately from learned YOLO defect classes.

## Local run

```bash
cp .env.example .env
pip install -e ".[ml,dev]"
uvicorn backend.app.main:app --reload
```

OpenAPI documentation is available at `/docs`.

SQLite is the local default. For PostgreSQL, set `DATABASE_URL=postgresql+psycopg://pcb_aoi:password@db:5432/pcb_aoi`.

## Storage

Inspection images are written under `reports/inspections/<inspection-id>/`. The database stores paths and structured results. Production deployments should replace local storage with durable object storage and add authentication, authorization, malware scanning, retention policy, migrations, and queue-based inference.

## Prototype notice

This backend is an academic/research prototype. Severity rules are configurable engineering policy examples, not certified acceptance criteria.
