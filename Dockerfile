# Multi-stage Dockerfile for job-scraper
# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY resume.txt ./

# Create non-root user
RUN useradd --no-create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app

USER appuser

# Add local pip packages to PATH
ENV PATH=/root/.local/bin:$PATH

# Environment variables (override at runtime)
ENV DATABASE_URL=sqlite:///./jobs.db
ENV REDIS_URL=redis://redis:6379/0
ENV MATCH_THRESHOLD=0.15
ENV MATCH_RETENTION_DAYS=3
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]