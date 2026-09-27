# Deploying to Google Cloud Run

The root `Dockerfile` builds the React dashboard and the FastAPI + YOLO11 backend into one
image. Cloud Run runs that image, serves the dashboard and API on one URL, scales to zero
when idle (free tier covers a demo workload), and downloads the weights on cold start from
`MODEL_URL` (verified against the sha256 in `models/model_card.json`).

## One-time setup

1. Google Cloud account with billing enabled (card required; the free tier is not charged).
2. Install the Google Cloud CLI and run `gcloud init`.
3. Create a project in the console (e.g. `pcb-aoi-demo`) and link it to the billing account.

```bash
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

## Deploy (from the repository root; rerun after every change)

```bash
gcloud run deploy pcb-aoi --source . --region us-central1 --allow-unauthenticated ^
  --memory 2Gi --cpu 2 --timeout 120 --max-instances 1 --cpu-boost ^
  --set-env-vars MODEL_URL=https://huggingface.co/shreya246/pcb-yolo11m/resolve/main/yolo11m_official_v4.pt
```

(`^` continues a line in Windows cmd/PowerShell; use `\` on macOS/Linux.)
The first build takes ~10 minutes. The command prints the service URL; `/api/model` and
`/health` are available on it.

## Persistent history

Cloud Run's disk is temporary, so the database and inspection images are kept outside the container:

- Database: a free [Neon](https://neon.tech) PostgreSQL project. Store its connection string (with the
  `postgresql+psycopg://` prefix) in Secret Manager as `pcb-aoi-database-url` and grant the Cloud Run
  service account `roles/secretmanager.secretAccessor`.
- Images and PDFs: a Cloud Storage bucket mounted at `/app/data` (the app's `STORAGE_ROOT` parent).

```bash
gcloud secrets create pcb-aoi-database-url --data-file=db.txt
gcloud storage buckets create gs://<bucket> --location=us-central1
gcloud run deploy pcb-aoi --source . --region us-central1 --allow-unauthenticated ^
  --memory 2Gi --cpu 2 --timeout 120 --max-instances 1 --cpu-boost ^
  --set-secrets DATABASE_URL=pcb-aoi-database-url:latest ^
  --add-volume name=data,type=cloud-storage,bucket=<bucket> --add-volume-mount volume=data,mount-path=/app/data
```

## Notes

- Cold start ~30 s; warm requests take 2-5 s on CPU. Weights are baked into the image.
- `--max-instances 1` caps cost; `.gcloudignore` keeps datasets, runs and weights out of the upload.
- `docker-compose.yml` is unchanged for local multi-service runs.
