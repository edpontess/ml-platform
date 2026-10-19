FROM python:3.12-slim

# Copy the uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY src/ ./src/

# Make our Python package importable
ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "ml_platform.api:app", "--host", "0.0.0.0", "--port", "8000"]