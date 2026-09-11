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

## Production gaps

Before production use, add authentication and authorization, TLS, a secrets manager, object storage, upload malware scanning, rate limits, background inference workers, observability, backups, signed reports, retention controls, model approval gates, and validated camera/calibration procedures.

The API Docker image installs the optional ML stack by default. For API-only
development, `docker build --build-arg INSTALL_ML=false -t pcb-aoi-api .` omits it;
that image cannot run YOLO. Trained weights still must be supplied separately.
The Vite development server proxies `/api` and `/health` to port 8000.
