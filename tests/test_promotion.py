from unittest.mock import MagicMock, patch

from ml_platform import promote_model
from ml_platform.promote_model import should_promote


def metrics(f1, precision=0.95, recall=0.95):
    return {
        "f1_macro": f1,
        "precision_macro": precision,
        "recall_macro": recall,
    }


def test_promotes_better_model():
    champion = metrics(0.93)
    candidate = metrics(0.95)

    assert should_promote(candidate, champion)


def test_rejects_small_improvement():
    champion = metrics(0.94)
    candidate = metrics(0.945)

    assert not should_promote(candidate, champion)


def test_rejects_worse_model():
    champion = metrics(0.95)
    candidate = metrics(0.93)

    assert not should_promote(candidate, champion)


def test_rejects_low_precision():
    candidate = metrics(0.97, precision=0.85)

    assert not should_promote(candidate, metrics(0.93))


def test_rejects_low_recall():
    candidate = metrics(0.97, recall=0.85)

    assert not should_promote(candidate, metrics(0.93))


def test_promotes_first_champion():
    candidate = metrics(0.95)

    assert should_promote(candidate, None)


def test_rejects_first_champion_below_threshold():
    candidate = metrics(0.95, precision=0.85)

    assert not should_promote(candidate, None)


def test_promotes_candidate_in_registry():
    with (
        patch.object(promote_model.mlflow, "set_tracking_uri"),
        patch.object(promote_model, "MlflowClient") as client_class,
        patch.object(promote_model, "load_train_validation") as load_data,
        patch.object(promote_model, "load_registered_model") as load_model,
        patch.object(promote_model, "evaluate_model") as evaluate,
    ):
        client = client_class.return_value
        client.get_model_version_by_alias.return_value = MagicMock(version="1")

        load_data.return_value = ("X_train", "X_val", "y_train", "y_val")

        load_model.side_effect = [
            "candidate-model",
            "champion-model",
        ]

        evaluate.side_effect = [
            metrics(0.96),
            metrics(0.93),
        ]

        promote_model.main("2")

        client.set_registered_model_alias.assert_called_once_with(
            "human-activity-classifier",
            "champion",
            "2",
        )


def test_does_not_promote_worse_candidate():
    with (
        patch.object(promote_model.mlflow, "set_tracking_uri"),
        patch.object(promote_model, "MlflowClient") as client_class,
        patch.object(promote_model, "load_train_validation") as load_data,
        patch.object(promote_model, "load_registered_model") as load_model,
        patch.object(promote_model, "evaluate_model") as evaluate,
    ):
        client = client_class.return_value
        client.get_model_version_by_alias.return_value = MagicMock(version="1")

        load_data.return_value = ("X_train", "X_val", "y_train", "y_val")

        load_model.side_effect = [
            "candidate-model",
            "champion-model",
        ]

        evaluate.side_effect = [
            metrics(0.92),
            metrics(0.95),
        ]

        promote_model.main("2")

        client.set_registered_model_alias.assert_not_called()
