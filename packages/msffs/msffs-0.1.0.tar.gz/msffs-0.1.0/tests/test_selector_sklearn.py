import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from msffs.selector import MSFFSSelector


def test_selector_pipeline_reduces_features():
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

    selector = MSFFSSelector(
        k=2,
        estimator=SVC(),
        grid_params={"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2},
    )

    pipe = Pipeline([("scale", StandardScaler()), ("select", selector)])
    X_selected = pipe.fit_transform(X, y)

    assert X_selected.shape[1] == 2


def test_selector_pipeline_defaults_work():
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

    selector = MSFFSSelector(k=2)
    pipe = Pipeline([("select", selector)])
    X_selected = pipe.fit_transform(X, y)

    assert X_selected.shape[1] == 2
