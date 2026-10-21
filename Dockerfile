FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/

# Package the approved model with the application.
COPY models/champion/ ./models/champion/

ENV PYTHONPATH=/app/src
ENV PATH="/app/.venv/bin:$PATH"

# Load the packaged model instead of contacting MLflow.
ENV MODEL_URI=/app/models/champion

EXPOSE 8000

CMD ["uvicorn", "ml_platform.api:app", "--host", "0.0.0.0", "--port", "8000"]