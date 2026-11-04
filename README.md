# ML Platform

A machine learning pipeline for Human Activity Recognition (UCI HAR dataset), using
MLflow for experiment tracking/model registry and FastAPI for model serving.

## Prerequisites

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- [Docker](https://www.docker.com/) (only for running the API in a container)
- [AWS CLI](https://aws.amazon.com/cli/) and [Terraform](https://www.terraform.io/) (only for the AWS deployment, step 8)

## Contents

- [Project layout](#project-layout)
- [Pipeline overview](#pipeline-overview)
- [Setup](#setup)
- Local pipeline: [1. MLflow server](#1-start-the-mlflow-tracking-server), [2. Train](#2-train-a-model), [3. Register](#3-register-the-best-model), [4. Promote](#4-promote-the-model-to-champion), [5. Try locally](#5-try-the-registered-model-locally)
- Serving: [6. Local API](#6-serve-the-model-via-the-api-local), [7. Docker](#7-serve-the-model-via-the-api-docker)
- Deployment: [8. AWS ECS Fargate](#8-deploy-to-aws-ecs-fargate)
- [API reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Running tests](#running-tests)

## Project layout

| Path | Purpose |
| --- | --- |
| `src/ml_platform/train.py` | Trains a model and logs it to MLflow |
| `src/ml_platform/register_model.py` | Registers the best run in the Model Registry |
| `src/ml_platform/promote_model.py` | Promotes a candidate version to `champion` |
| `src/ml_platform/load_model.py` | Loads the `champion` model and predicts locally |
| `src/ml_platform/export_model.py` | Exports the `champion` model to `models/champion/` for the standalone image |
| `src/ml_platform/api.py` | FastAPI app serving the `champion` model |
| `src/ml_platform/test_api_manual.py` | Sends a sample test-split row to a running API (`API_URL`, default `http://127.0.0.1:8000`) |
| `tests/` | Unit tests |
| `Dockerfile` | Image for the API |
| `models/champion/` | Exported `champion` model packaged into the standalone image |
| `infrastructure/terraform/` | AWS infrastructure (ECR, ECS Fargate, IAM, networking, logs) |
| `data/` | UCI HAR dataset |

## Pipeline overview

```
train -> register -> promote (champion) -> export -> build image -> push to ECR -> run on ECS Fargate
                                              \-> serve locally (uvicorn or Docker)
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

## 8. Deploy to AWS ECS Fargate

The standalone image is deployed to ECS Fargate (`eu-north-1`) with Terraform. Only the
standalone image is used, so MLflow is not needed in AWS.

### Prerequisites

- Terraform (version pinned in [.terraform-version](infrastructure/terraform/.terraform-version)).
- An AWS CLI profile named `ml-platform` (the default `aws_profile`). Verify it with:

  ```bash
  aws sts get-caller-identity --profile ml-platform
  ```

- Credentials come from the AWS profile only. Do not commit keys (`access_key`, `*.tfstate`
  and `*.tfvars` are gitignored).

### What Terraform creates

| Resource | File | Notes |
| --- | --- | --- |
| ECR repository | `ecr.tf` | Holds the API image |
| ECS cluster, task definition, service | `ecs.tf` | Fargate, ARM64, 0.5 vCPU / 1 GB, public IP |
| IAM execution role | `iam.tf` | Lets ECS pull from ECR and write logs |
| Security group, default VPC lookup | `network.tf` | Inbound `8000` only from `allowed_client_cidr` |
| CloudWatch log group | `cloudwatch.tf` | `/ecs/ml-platform-api`, 7-day retention |

The service runs in the default VPC with a public IP and no load balancer, so the IP changes
every time the task restarts.

### Variables

All values live in [variables.tf](infrastructure/terraform/variables.tf). The commonly changed ones:

| Variable | Default | Purpose |
| --- | --- | --- |
| `allowed_client_cidr` | none (required) | Your public IP with `/32`, e.g. `203.0.113.10/32` |
| `image_tag` | `v1` | ECR image tag the task runs |
| `desired_count` | `1` | Number of running tasks |
| `task_cpu` / `task_memory` | `512` / `1024` | Fargate task size |
| `container_port` | `8000` | Port exposed by the container and security group |
| `project_name` / `environment` | `ml-platform` / `dev` | Resource tags |

Set the required variable without committing it, either on the command line or in a
`terraform.tfvars` file (gitignored):

```bash
export TF_VAR_allowed_client_cidr="$(curl -s https://checkip.amazonaws.com)/32"
```

### Deploy

```bash
cd infrastructure/terraform
terraform init

# 1. Create the ECR repository first so there is somewhere to push
terraform apply -target=aws_ecr_repository.ml_platform_api

# 2. Log in to ECR, then build and push the image (the task runs on ARM64)
ECR_URL=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region eu-north-1 --profile ml-platform \
  | docker login --username AWS --password-stdin "${ECR_URL%%/*}"

cd ../..
docker build --platform linux/arm64 -t "$ECR_URL:v1" .
docker push "$ECR_URL:v1"

# 3. Create the remaining infrastructure
cd infrastructure/terraform
terraform apply
```

To release a new version, push a new tag (e.g. `v2`) and apply with `-var image_tag=v2`.

### Find the API address and test it

```bash
TASK=$(aws ecs list-tasks --cluster ml-platform-cluster --service-name ml-platform-api-service \
  --region eu-north-1 --profile ml-platform --query 'taskArns[0]' --output text)

ENI=$(aws ecs describe-tasks --cluster ml-platform-cluster --tasks "$TASK" \
  --region eu-north-1 --profile ml-platform \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value" --output text)

aws ec2 describe-network-interfaces --network-interface-ids "$ENI" \
  --region eu-north-1 --profile ml-platform \
  --query 'NetworkInterfaces[0].Association.PublicIp' --output text
```

Then call the API from the allowed IP:

```bash
curl http://<PUBLIC_IP>:8000/health
API_URL=http://<PUBLIC_IP>:8000 uv run python -m ml_platform.test_api_manual
```

Logs are in the CloudWatch log group `/ecs/ml-platform-api`.

### Stop, start and tear down

Fargate bills while a task is running. Scale to zero when not in use:

```bash
aws ecs update-service --cluster ml-platform-cluster --service ml-platform-api-service \
  --desired-count 0 --region eu-north-1 --profile ml-platform
```

Use `--desired-count 1` to start it again. Terraform owns `desired_count`, so the next
`terraform apply` resets it to the variable value. To remove everything:

```bash
terraform destroy
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
| ECS task stops immediately with `exec format error` | Image was built for the wrong architecture; rebuild with `--platform linux/arm64` |
| ECS `CannotPullContainerError` | The `image_tag` is not in ECR; push the image, then re-apply |
| API request times out on AWS | Your IP changed; update `allowed_client_cidr` and re-apply, or the task is scaled to 0 |
| Public IP no longer works | Task restarted and got a new IP; look it up again (step 8) |
| `terraform plan` asks for `allowed_client_cidr` or fails validation | Provide a valid IPv4 with a `/32` suffix |

## Running tests

```bash
uv run pytest
```