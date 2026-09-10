# Pinned base image: never python:latest, so builds are reproducible.
FROM python:3.12.8-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

# Unprivileged runtime user (rarely changes, so this layer stays cached).
RUN useradd --create-home --uid 10001 appuser

# Dependencies first: this layer is reused until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code last: editing app.py only rebuilds from here.
COPY VERSION app.py ./

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health')" || exit 1

# Bind to 0.0.0.0 so the port is reachable from outside the container.
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

# OCI metadata. Declared last because these values change on every build
# and must not invalidate the cached dependency layers above.
ARG APP_VERSION=dev
ARG VCS_REF=unknown
ARG BUILD_DATE=unknown
ARG SOURCE_URL=https://github.com/Abdullah8168/student-ml-api
LABEL org.opencontainers.image.title="student-ml-api" \
      org.opencontainers.image.description="ML inference API (FastAPI)" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.source="${SOURCE_URL}" \
      org.opencontainers.image.url="${SOURCE_URL}"
