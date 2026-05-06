# ── stalk. backend image (FastAPI on Python 3.11) ───────────────────────────
FROM python:3.11-slim

# Avoid .pyc clutter and unbuffered logs (so Koyeb shows logs in real time)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system deps required by psycopg2-binary and pandas/numpy wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first so this layer caches across code changes
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy backend source
COPY backend/ /app/

# Koyeb injects $PORT — default to 8000 for local docker run
ENV PORT=8000
EXPOSE 8000

# Healthcheck — Koyeb will hit /ping
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/ping || exit 1

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
