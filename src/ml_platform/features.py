from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from ml_platform.config import TrainingConfig


def build_pipeline(config: TrainingConfig):
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=config.C,
                    max_iter=config.max_iter,
                    random_state=config.random_state,
                ),
            ),
        ]
    )
