import mlflow
from mlflow import MlflowClient

TRACKING_URI = "http://127.0.0.1:5001"
EXPERIMENT_NAME = "human-activity-recognition"
MODEL_NAME = "human-activity-classifier"


def main():
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient()

    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)

    if experiment is None:
        raise RuntimeError("Experiment not found")

    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.f1_macro DESC"],
    )

    # Keep only runs that have an F1 score.
    runs = runs.dropna(subset=["metrics.f1_macro"])

    if runs.empty:
        raise RuntimeError("No evaluated runs found")

    best_run = runs.iloc[0]
    run_id = best_run["run_id"]
    f1 = best_run["metrics.f1_macro"]

    print(f"Best run: {run_id}")
    print(f"Validation F1: {f1:.4f}")

    # Register the model artifact from the selected run.
    model_uri = f"runs:/{run_id}/model"

    registered_model = mlflow.register_model(
        model_uri=model_uri,
        name=MODEL_NAME,
    )

    print(f"Registered model version: {registered_model.version}")


if __name__ == "__main__":
    main()
