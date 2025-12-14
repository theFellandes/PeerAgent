# Production Dockerfile for FastAPI Application
# Multi-stage build for smaller final image

# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.11-slim AS builder

# Build arguments
ARG VERSION=1.2.0

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Create wheels for dependencies
RUN pip wheel --no-deps --wheel-dir /build/wheels -r requirements.txt

# =============================================================================
# Stage 2: Runtime
# =============================================================================
FROM python:3.11-slim AS runtime

# Build arguments
ARG VERSION=1.2.0

# Labels for image metadata
LABEL org.opencontainers.image.title="PeerAgent API" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.description="Multi-Agent AI System with LangGraph" \
      org.opencontainers.image.authors="theFellandes" \
      org.opencontainers.image.source="https://github.com/theFellandes/PeerAgent"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_VERSION=${VERSION} \
    # Gunicorn settings
    WORKERS=4 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker \
    TIMEOUT=120 \
    KEEPALIVE=5 \
    MAX_REQUESTS=1000 \
    MAX_REQUESTS_JITTER=50

# Set work directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY src/ ./src/
COPY main.py .

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser \
    && chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ping || exit 1

# Run the application with gunicorn for production
CMD ["sh", "-c", "gunicorn src.api.main:app \
    --workers ${WORKERS} \
    --worker-class ${WORKER_CLASS} \
    --timeout ${TIMEOUT} \
    --keep-alive ${KEEPALIVE} \
    --max-requests ${MAX_REQUESTS} \
    --max-requests-jitter ${MAX_REQUESTS_JITTER} \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -"]

# Alternative: Run with uvicorn directly for development
# CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
