import numpy as np
from sklearn.svm import SVC

from msffs._msffs_impl import msffs_run
from msffs.api import msffs_select


def test_regression_behavior_matches_impl():
    X = np.array(
        [
            [0.1, 0.2, 0.3, 0.4],
            [0.2, 0.1, 0.4, 0.3],
            [0.9, 0.8, 0.7, 0.6],
            [0.8, 0.9, 0.6, 0.7],
            [0.05, 0.15, 0.25, 0.35],
            [0.85, 0.75, 0.65, 0.55],
        ]
    )
    y = np.array([0, 0, 1, 1, 0, 1])

    grid_params = {"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2}

    impl = msffs_run(
        X=X,
        y=y,
        max_f=2,
        estimator=SVC(),
        grid_params=grid_params,
    )

    api = msffs_select(
        X,
        k=2,
        y=y,
        estimator=SVC(),
        grid_params=grid_params,
    )

    assert api["winner_list"] == impl["winner_list"]
    assert np.allclose(api["best_scores"], impl["best_scores"])
    assert np.array_equal(api["selected_indices"], impl["winner_list"][2])
