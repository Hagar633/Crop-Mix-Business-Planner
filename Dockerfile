# =============================================================================
# Crop Mix Business Planner - Production Dockerfile for Azure Deployment
# Base Image: Official Python 3.10 Slim Linux
# =============================================================================

FROM python:3.10-slim as builder

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies for C++/Fortran HiGHS solver bindings & curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code and install application package
COPY src/ /app/src/
COPY run_ui.py /app/
RUN pip install --no-cache-dir -e .

# Expose web server port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/preset || exit 1

# Production entrypoint using Gunicorn with Uvicorn workers
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "src.crop_mix.app:app", "--bind", "0.0.0.0:8000"]
