FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy dependency files first for better layer caching
COPY --chown=appuser:appuser pyproject.toml uv.lock* ./

# Install dependencies (skip project installation for now)
RUN uv sync --frozen --no-install-project

# Copy application code
COPY --chown=appuser:appuser . .

# Install the project itself
RUN uv sync --frozen

# Switch to non-root user
USER appuser

CMD ["uv", "run", "python", "-m", "nlp.worker.consumer"]
