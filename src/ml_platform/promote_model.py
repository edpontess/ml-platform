import argparse

import mlflow
import mlflow.pyfunc
from mlflow import MlflowClient

from ml_platform.data import load_train_validation
from ml_platform.evaluate import evaluate_model

TRACKING_URI = "http://127.0.0.1:5001"
MODEL_NAME = "human-activity-classifier"

MIN_F1_IMPROVEMENT = 0.01
MIN_PRECISION = 0.90
MIN_RECALL = 0.90


def should_promote(candidate_metrics, champion_metrics):
    if (
        candidate_metrics["precision_macro"] < MIN_PRECISION
        or candidate_metrics["recall_macro"] < MIN_RECALL
    ):
        return False

    if champion_metrics is None:
        return True

    return (
        candidate_metrics["f1_macro"] - champion_metrics["f1_macro"]
        >= MIN_F1_IMPROVEMENT
    )


def load_registered_model(version: str):
    model_uri = f"models:/{MODEL_NAME}/{version}"
    return mlflow.pyfunc.load_model(model_uri)


def main(candidate_version: str):
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    # Load the same validation data for both models.
    _X_train, X_val, _y_train, y_val = load_train_validation(
        test_size=0.2,
        random_state=42,
    )

    # Load candidate model.
    candidate = load_registered_model(candidate_version)
    candidate_metrics = evaluate_model(candidate, X_val, y_val)

    print(f"Candidate version: {candidate_version}")
    print(f"Candidate metrics: {candidate_metrics}")

    # Find current champion, if one exists.
    try:
        champion_version = client.get_model_version_by_alias(
            MODEL_NAME,
            "champion",
        ).version
    except mlflow.exceptions.MlflowException as exc:
        if "not found" not in str(exc).lower():
            raise
        champion_version = None

    if champion_version is None:
        print("No champion exists. Checking minimum thresholds.")

        if should_promote(candidate_metrics, None):
            client.set_registered_model_alias(
                MODEL_NAME,
                "champion",
                candidate_version,
            )
            print("First champion promoted.")
        else:
            print("Candidate rejected: minimum thresholds not met.")

        return

    if str(champion_version) == str(candidate_version):
        print("Candidate is already the champion.")
        return

    # Evaluate current champion on exactly the same data.
    champion = load_registered_model(champion_version)
    champion_metrics = evaluate_model(champion, X_val, y_val)

    print(f"Champion version: {champion_version}")
    print(f"Champion metrics: {champion_metrics}")

    f1_improvement = candidate_metrics["f1_macro"] - champion_metrics["f1_macro"]

    print(f"F1 improvement: {f1_improvement:+.4f}")

    if should_promote(candidate_metrics, champion_metrics):
        client.set_registered_model_alias(
            MODEL_NAME,
            "champion",
            candidate_version,
        )
        print(f"Promoted version {candidate_version} to champion.")
    else:
        print("Candidate rejected. Champion remains unchanged.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--candidate-version",
        required=True,
        help="Registered model version to evaluate",
    )
    args = parser.parse_args()

    main(args.candidate_version)
