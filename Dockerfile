# Builds the React dashboard and the FastAPI + YOLO backend into one image.
# Used by docker-compose (API only is exercised there) and by Hugging Face Spaces
# (the same image also serves the dashboard on PORT).

FROM node:22-alpine AS frontend
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    HOME=/home/aoi \
    DATABASE_URL=sqlite:////app/data/pcb_aoi.db \
    STORAGE_ROOT=/app/data/inspections \
    MODEL_PATH=/app/models/weights/yolo11m_official_v4.pt \
    MODEL_CARD_PATH=/app/models/model_card.json \
    SEVERITY_POLICY_PATH=/app/backend/app/core/severity.yaml \
    STATIC_DIR=/app/frontend/dist \
    YOLO_CONFIG_DIR=/home/aoi/.config/Ultralytics

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
RUN groupadd --system --gid 1000 aoi && useradd --system --uid 1000 --gid aoi --create-home aoi

COPY pyproject.toml README.md alembic.ini ./
COPY backend ./backend
COPY src ./src
COPY migrations ./migrations
COPY scripts/download_weights.py ./scripts/download_weights.py
COPY models/model_card.json ./models/model_card.json
# Bake the served weights into the image so cold starts never depend on an external download.
COPY models/weights/yolo11m_official_v4.pt ./models/weights/yolo11m_official_v4.pt
ARG INSTALL_ML=true
RUN pip install --upgrade pip && pip install -e ".[postgres]" && \
    if [ "$INSTALL_ML" = "true" ]; then \
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
        pip install -e ".[ml]"; \
    fi && \
    mkdir -p /app/data/inspections /app/models/weights /home/aoi/.config/Ultralytics && \
    chown -R aoi:aoi /app /home/aoi
COPY --from=frontend --chown=aoi:aoi /ui/dist ./frontend/dist

USER aoi
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health', timeout=3)" || exit 1

CMD ["sh", "-c", "python scripts/download_weights.py && alembic upgrade head && exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${API_WORKERS:-1}"]
