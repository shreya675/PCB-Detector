# Deployment

## Development

```bash
cp .env.example .env
pip install -e ".[dev]"
alembic upgrade head
uvicorn backend.app.main:app --reload
cd frontend && npm install && npm run dev
```

## Containers

```bash
cp .env.example .env
# Change POSTGRES_PASSWORD before shared deployment.
docker compose up --build
```

Dashboard: `http://localhost:8080`  
API: `http://localhost:8000`  
OpenAPI: `http://localhost:8000/docs`

The API image uses a non-root user, runs migrations before startup, exposes a health check, and stores reports in a named volume. Model weights are mounted read-only. Nginx serves the SPA and proxies API requests.

## Cloud

The hosted demo runs on Google Cloud Run from the same Dockerfile; see deployment-cloud-run.md.

## Hardening

For multi-user or production use, add authentication, TLS, object storage for images and reports, rate limiting and background inference workers.

The API Docker image installs the optional ML stack by default. For API-only
development, `docker build --build-arg INSTALL_ML=false -t pcb-aoi-api .` omits it;
that image cannot run YOLO. Weights are copied into the image when present in `models/weights/`.
The Vite development server proxies `/api` and `/health` to port 8000.
