from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("data/human+activity+recognition+using+smartphones/UCI HAR Dataset")


def load_split(split: str):
    if split not in {"train", "test"}:
        raise ValueError("split must be 'train' or 'test'")

    folder = DATA_DIR / split

    X = pd.read_csv(
        folder / f"X_{split}.txt",
        sep=r"\s+",
        header=None,
    )

    y = pd.read_csv(
        folder / f"y_{split}.txt",
        sep=r"\s+",
        header=None,
    ).iloc[:, 0]

    subjects = pd.read_csv(
        folder / f"subject_{split}.txt",
        sep=r"\s+",
        header=None,
    ).iloc[:, 0]

    if len(X) != len(y) or len(X) != len(subjects):
        raise ValueError("Feature, label and subject counts differ")

    if X.isna().any().any() or y.isna().any():
        raise ValueError("Dataset contains missing values")

    if not np.isfinite(X.to_numpy()).all():
        raise ValueError("Dataset contains non-finite features")

    return X, y, subjects