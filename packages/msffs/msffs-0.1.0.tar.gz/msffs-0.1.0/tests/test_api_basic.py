import numpy as np
from sklearn.svm import SVC

from msffs.api import msffs_select


def test_api_basic_returns_expected_keys():
    X = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.2, 0.1, 0.4],
            [0.9, 0.8, 0.7],
            [0.8, 0.9, 0.6],
        ]
    )
    y = np.array([0, 0, 1, 1])

    result = msffs_select(
        X,
        k=2,
        y=y,
        estimator=SVC(),
        grid_params={"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2},
    )

    assert "selected_indices" in result
    assert "best_scores" in result
    assert "winner_list" in result
    assert "best_params_list" in result
    assert result["selected_indices"].shape[0] == 2


def test_api_defaults_work():
    X = np.array(
        [
            [0.1, 0.2, 0.3],
            [0.2, 0.1, 0.4],
            [0.15, 0.25, 0.35],
            [0.9, 0.8, 0.7],
            [0.8, 0.9, 0.6],
            [0.85, 0.75, 0.65],
        ]
    )
    y = np.array([0, 0, 0, 1, 1, 1])

    result = msffs_select(X, k=2, y=y)

    assert result["selected_indices"].shape[0] == 2
