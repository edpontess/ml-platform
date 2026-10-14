from ml_platform import get_project_name


def test_project_name():
    assert get_project_name() == "ML Platform"
