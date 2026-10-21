import argparse
import os
import shutil
from pathlib import Path

import mlflow
from mlflow import MlflowClient

MODEL_NAME = "human-activity-classifier"
OUTPUT_DIR = Path("models/champion")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv(
            "MLFLOW_TRACKING_URI",
            "http://127.0.0.1:5001",
        ),
    )
    args = parser.parse_args()

    mlflow.set_tracking_uri(args.tracking_uri)

    client = MlflowClient()
    champion = client.get_model_version_by_alias(
        MODEL_NAME,
        "champion",
    )

    model_uri = f"models:/{MODEL_NAME}/{champion.version}"

    print(f"Exporting model version {champion.version}")
    print(f"Source run: {champion.run_id}")

    # Download the complete MLflow model directory.
    downloaded_path = Path(
        mlflow.artifacts.download_artifacts(
            artifact_uri=model_uri,
        )
    )

    OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    shutil.copytree(downloaded_path, OUTPUT_DIR)

    print(f"Model exported to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()