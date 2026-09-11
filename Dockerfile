FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*
RUN groupadd --system aoi && useradd --system --gid aoi --create-home aoi

COPY pyproject.toml README.md alembic.ini ./
COPY backend ./backend
COPY src ./src
COPY migrations ./migrations
ARG INSTALL_ML=true
RUN pip install --upgrade pip && pip install -e ".[postgres]" && \
    if [ "$INSTALL_ML" = "true" ]; then pip install -e ".[ml]"; fi && \
    mkdir -p /app/reports/inspections /app/models/weights && \
    chown -R aoi:aoi /app

USER aoi
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers ${API_WORKERS:-1}"]
