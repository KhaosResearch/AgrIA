FROM python:3.12-slim

# Set working directory
WORKDIR /agria_app

# Python & UV optimization flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_CACHE_DIR=/agria_app/.uv_cache

# Install minimal OS requirements for git dependencies and builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Pull UV binary globally
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Leverage Docker cache for dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Expose the API port
EXPOSE 5000

# Run directly through uv (async mode)
CMD ["uv", "run", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]