# mSFFS
mSFFS (Modified Sequential Floating Forward Selection) is a Python library for feature selection, offering a simple functional API and a scikit-learn–compatible transformer.

## Install

```bash
pip install msffs
```

## Minimal usage (defaults)

```python
import numpy as np
from msffs import msffs_select

X = np.array(
    [
        [0.1, 0.2, 0.3, 0.4],
        [0.2, 0.1, 0.4, 0.3],
        [0.15, 0.25, 0.35, 0.45],
        [0.9, 0.8, 0.7, 0.6],
        [0.8, 0.9, 0.6, 0.7],
        [0.85, 0.75, 0.65, 0.55],
    ]
)
y = np.array([0, 0, 0, 1, 1, 1])

result = msffs_select(X, k=2, y=y)
print(result["selected_indices"])
```

## Scikit-learn pipeline usage

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from msffs import MSFFSSelector

pipe = Pipeline(
    steps=[
        ("scale", StandardScaler()),
        (
            "select",
            MSFFSSelector(
                k=2,
                estimator=SVC(),
                grid_params={"param_grid": {"C": [1.0], "kernel": ["linear"]}, "cv": 2},
            ),
        ),
    ]
)

X_selected = pipe.fit_transform(X, y)
```

## API overview

- `msffs_select(X, k, y, estimator=None, grid_params=None)` returns a dict with:
  - `selected_indices`: indices of the selected features
  - `selected_X`: `X` subset to selected features (when available)
  - `best_scores`: cross-validated scores by subset size
  - `winner_list`: selected feature indices by subset size
  - `best_params_list`: best estimator params by subset size
- `MSFFSSelector`: scikit-learn compatible transformer for pipelines.

Defaults:
- Estimator: `sklearn.linear_model.LogisticRegression(max_iter=1000, random_state=0)`
- Grid params:
  - `C`: [0.1, 1.0, 10.0]
  - `cv`: 3

## Notes

- mSFFS is supervised, so `y` is required.
- For very small datasets, reduce CV folds via `grid_params={"cv": 2, ...}`.
- Defaults stay lightweight and deterministic; pass any sklearn-compatible estimator
  when you need something heavier (e.g., XGBoost).
  
## Development

```bash
pip install -e ".[dev,test]"
ruff check .
black --check .
pytest
python -m build
```

## Citation

If you use this library in academic work, please cite:

- J. Li, D. De Ridder, D. Adhia, M. Hall, R. Mani and J. D. Deng, "Modified Feature
  Selection for Improved Classification of Resting-State Raw EEG Signals in Chronic
  Knee Pain," in IEEE Transactions on Biomedical Engineering, vol. 72, no. 5,
  pp. 1688-1696, May 2025, doi: 10.1109/TBME.2024.3517659.
