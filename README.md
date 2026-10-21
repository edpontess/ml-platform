# ML Platform

A machine learning pipeline for Human Activity Recognition (UCI HAR dataset), using
MLflow for experiment tracking/model registry and FastAPI for model serving.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- [Docker](https://www.docker.com/) (only for running the API in a container)

## Project layout

| Path | Purpose |
| --- | --- |
| `src/ml_platform/train.py` | Trains a model and logs it to MLflow |
| `src/ml_platform/register_model.py` | Registers the best run in the Model Registry |
| `src/ml_platform/promote_model.py` | Promotes a candidate version to `champion` |
| `src/ml_platform/load_model.py` | Loads the `champion` model and predicts locally |
| `src/ml_platform/export_model.py` | Exports the `champion` model to `models/champion/` for the standalone image |
| `src/ml_platform/api.py` | FastAPI app serving the `champion` model |
| `tests/` | Unit tests |
| `Dockerfile` | Image for the API |
| `data/` | UCI HAR dataset |

## Pipeline overview

```
train -> register -> promote (champion) -> serve (local or Docker)
```

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

If you plan to run the API in Docker (step 7), the container must be able to reach the
server. Start it on all interfaces and allow the `host.docker.internal` host instead:

```bash
uv run mlflow server \
  --backend-store-uri sqlite:///mlflow.db \
  --artifacts-destination ./mlartifacts \
  --host 0.0.0.0 \
  --port 5001 \
  --allowed-hosts "localhost:*,127.0.0.1:*,host.docker.internal:*"
```

> The `Host` header includes the port, so entries need a `:*` wildcard. Without it
> MLflow rejects requests with `403 Invalid Host header`.

Keep this running in its own terminal. The UI is available at http://127.0.0.1:5001.
Stop it with `Ctrl+C`.

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

## 6. Serve the model via the API (local)

The API loads `models:/human-activity-classifier@champion` at startup, so steps 1-4 must
be done first. It reads the tracking server from `MLFLOW_TRACKING_URI` (default
`http://127.0.0.1:5000`), so set it to the port used above:

```bash
MLFLOW_TRACKING_URI=http://127.0.0.1:5001 \
  uv run uvicorn ml_platform.api:app --host 127.0.0.1 --port 8000
```

## 7. Serve the model via the API (Docker)

There are two ways to run the API in a container. They differ in where the model comes from.

| Image | Model source | Needs MLflow at runtime |
| --- | --- | --- |
| `ml-platform-api:standalone` | Packaged into the image from `models/champion/` | No |
| `ml-platform-api:latest` | Downloaded from the MLflow registry at startup | Yes |

The current [Dockerfile](Dockerfile) packages the model, so it builds the standalone image.
`latest` is the older image built before the model was packaged; it is only needed if you
want the container to pull the `champion` model from MLflow itself.

### Standalone image (recommended)

Export the current `champion` model from MLflow into `models/champion/` (the MLflow server
must be running):

```bash
uv run python -m ml_platform.export_model
```

Build and run. No MLflow server is needed once the image is built:

```bash
docker build -t ml-platform-api:standalone .

docker run --rm \
  --name ml-platform-api \
  -p 127.0.0.1:8000:8000 \
  ml-platform-api:standalone
```

Re-run the export and rebuild whenever the `champion` model changes.

### MLflow-backed image

Use the Docker variant of the MLflow server from step 1, then run:

```bash
docker run --rm \
  --name ml-platform-api \
  -p 127.0.0.1:8000:8000 \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5001 \
  ml-platform-api:latest
```

The container exits at startup if the tracking server is unreachable or no `champion`
version exists. The same behaviour is available from the standalone image by overriding
the model location at run time:

```bash
docker run --rm \
  --name ml-platform-api \
  -p 127.0.0.1:8000:8000 \
  -e MODEL_URI=models:/human-activity-classifier@champion \
  -e MLFLOW_TRACKING_URI=http://host.docker.internal:5001 \
  ml-platform-api:standalone
```

## API reference

- Health check: `GET http://localhost:8000/health`
- Prediction: `POST http://localhost:8000/predict` with a JSON body of exactly 561 finite floats:

```json
{
  "features": [0.1, 0.2, "... 561 float values ..."]
}
```

Response:

```json
{ "prediction": 4, "activity": "SITTING" }
```

Activities: `WALKING`, `WALKING_UPSTAIRS`, `WALKING_DOWNSTAIRS`, `SITTING`, `STANDING`, `LAYING`.

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `403 Invalid Host header` from MLflow | Add the caller's host with a port wildcard to `--allowed-hosts` (see step 1) |
| Container cannot reach MLflow | Start MLflow with `--host 0.0.0.0` and use `host.docker.internal` in `MLFLOW_TRACKING_URI` |
| `docker build` fails on `COPY models/champion/` | Run `uv run python -m ml_platform.export_model` first |
| Container exits with `Application startup failed` | No `champion` model registered; run steps 3-4 |
| Port 5000 conflicts on macOS | AirPlay Receiver uses it; this project uses 5001 |

## Running tests

```bash
uv run pytest
```


aws sts get-caller-identity --profile ml-platform