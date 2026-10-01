# =====================================================================
# Backend image — multi-stage
#   dev  : used by docker-compose (source bind-mounted, --reload)
#   prod : self contained image for running the API without a mount
# =====================================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# ---------------------------------------------------------------------
FROM base AS dev

COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------------
FROM base AS prod

COPY . .
RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
