# Deploying to Hugging Face Spaces

The root `Dockerfile` builds the React dashboard and the FastAPI + YOLO11 backend into one
image. On Spaces the API serves the dashboard itself, uses SQLite, and downloads the model
weights on first start from `MODEL_URL`.

## One-time setup

1. **Upload the weights** to a Hugging Face *model* repository (weights are not in git):
   `https://huggingface.co/new` → name it e.g. `pcb-aoi-yolo11m` → *Files* → *Add file* →
   upload `models/weights/yolo11m_official_v4.pt`. Note the download URL:
   `https://huggingface.co/<user>/pcb-aoi-yolo11m/resolve/main/yolo11m_official_v4.pt`
2. **Create the Space**: `https://huggingface.co/new-space` → SDK **Docker** → *Blank* → CPU basic (free).
3. In the Space **Settings → Variables and secrets** add a variable
   `MODEL_URL` = the download URL from step 1. (Optional: `CONFIDENCE_THRESHOLD=0.25`.)
4. Push the repository to the Space (it is a plain git remote):

   ```bash
   git remote add hf https://huggingface.co/spaces/<user>/<space-name>
   git push hf main
   ```
   Authenticate with a Hugging Face access token (write) when git asks for a password.

The first build takes ~10 minutes (PyTorch CPU wheels). The Space then serves the
dashboard at its public URL, `/api/model` shows the loaded checkpoint, and
`/health` reports readiness.

## Notes

- Free Spaces have ephemeral disk: inspection history and images reset when the Space restarts or sleeps.
- CPU inference of YOLO11m at 1024 px takes ~2-5 s per image.
- `scripts/download_weights.py` verifies the download against the sha256 in `models/model_card.json`.
- `docker-compose.yml` still runs the API, Postgres and an nginx frontend as separate services; it sets
  `STATIC_DIR=/nonexistent` so the API container does not also serve the dashboard there.
