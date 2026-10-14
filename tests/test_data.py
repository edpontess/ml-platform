from sklearn.model_selection import GroupShuffleSplit

from ml_platform.data import load_split


def test_subject_disjoint_split():
    X, y, subjects = load_split("train")

    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=0.2,
        random_state=42,
    )

    train_idx, val_idx = next(
        splitter.split(X, y, groups=subjects)
    )

    train_subjects = set(subjects.iloc[train_idx])
    val_subjects = set(subjects.iloc[val_idx])

    assert train_subjects.isdisjoint(val_subjects)
    assert train_subjects | val_subjects == set(subjects)