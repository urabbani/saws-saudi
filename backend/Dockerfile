# ==========================================
# SAWS Backend Dockerfile
# FastAPI + Python 3.12
# ==========================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build dependencies
    gcc \
    g++ \
    libpq-dev \
    # Geospatial dependencies
    binutils \
    libproj-dev \
    libgeos-dev \
    libgdal-dev \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements/base.txt requirements/geospatial.txt requirements/ ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r base.txt && \
    pip install -r geospatial.txt

# Install development dependencies (optional, for dev builds)
ARG DEV_MODE=false
RUN if [ "$DEV_MODE" = "true" ]; then \
    pip install -r dev.txt; \
    fi

# Copy application code
COPY . .

# Create directory for GEE credentials
RUN mkdir -p /app/config

# Create non-root user for running the application
RUN useradd -m -u 1000 saws && \
    chown -R saws:saws /app
USER saws

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
