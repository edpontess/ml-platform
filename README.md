# ML Platform

A machine learning pipeline for Human Activity Recognition (UCI HAR dataset), using
MLflow for experiment tracking/model registry and FastAPI for model serving.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

Install dependencies into a virtual environment:

```bash
uv sync
```

The UCI HAR dataset is already included under `data/human+activity+recognition+using+smartphones/`.

## 1. Start the MLflow tracking server

```bash
uv run mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --artifacts-destination ./mlartifacts \
  --host 127.0.0.1 \
  --port 5001
```

with docker:

uv run mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --artifacts-destination ./mlartifacts \
  --host 0.0.0.0 \
  --port 5001 \
  --allowed-hosts "localhost:*,127.0.0.1:*,host.docker.internal:*"

Keep this running in its own terminal. The UI is available at http://127.0.0.1:5001.

> Port 5000 is avoided because on macOS it's commonly used by the AirPlay Receiver
> (ControlCenter), which conflicts with MLflow.

## 2. Train a model

In a new terminal, run the training pipeline. This trains a model, evaluates it on a
held-out validation split, and logs params/metrics/artifacts to MLflow:

```bash
uv run python -m ml_platform.train
```

Note the `MLflow run ID` printed at the end of the output.

## 3. Register the best model

Finds the best run (by `f1_macro`) in the experiment and registers it in the MLflow
Model Registry as `human-activity-classifier`:

```bash
uv run python -m ml_platform.register_model
```

Note the registered model `version` printed in the output.

## 4. Promote the model to champion

Evaluates the candidate version against the current `champion` (if any) and promotes it
if it meets the minimum thresholds:

```bash
uv run python -m ml_platform.promote_model --candidate-version <VERSION>
```

## 5. Try the registered model locally

Loads the `champion` model and runs a few sample predictions from the test split:

```bash
uv run python -m ml_platform.load_model
```

## 6. Serve the model via the API

```bash
uv run uvicorn ml_platform.api:app --host 0.0.0.0 --port 8000
```

- Health check: `GET http://localhost:8000/health`
- Prediction: `POST http://localhost:8000/predict` with a JSON body:

```json
{
  "features": [0.1, 0.2, "... 561 float values ..."]
}
```

## Running tests

```bash
uv run pytest
```