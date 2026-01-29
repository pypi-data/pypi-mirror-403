import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from sklearn.model_selection import GridSearchCV

logger = logging.getLogger(__name__)


@dataclass
class _MsffsState:
    seen: set[frozenset[int]]
    best_scores: np.ndarray
    winner_list: list[list[int]]
    best_params_list: list[Any | None]


def _log(message: str) -> None:
    if logger:
        logger.info(message)


def tune_clf(
    X: np.ndarray,
    y: np.ndarray,
    estimator: Any,
    grid_params: dict[str, Any] | Mapping[str, Any],
):
    # Tune classifier with GridSearchCV using the provided estimator.

    if isinstance(grid_params, Mapping) and "param_grid" in grid_params:
        param_grid = grid_params["param_grid"]
        cv = grid_params.get("cv", 3)
        scoring = grid_params.get("scoring")
        n_jobs = grid_params.get("n_jobs")
        refit = grid_params.get("refit", True)
    else:
        param_grid = grid_params
        cv = 3
        scoring = None
        n_jobs = None
        refit = True

    clf = GridSearchCV(
        estimator,
        param_grid=param_grid,
        cv=cv,
        scoring=scoring,
        n_jobs=n_jobs,
        refit=refit,
    )
    return clf.fit(X, y)


def mSFFS_forward(X, y, estimator, grid_params, winner, score_best_i, state: _MsffsState):
    temp_winner = []
    best_params_i = None
    for new_member in range(X.shape[1]):
        if new_member in winner:
            continue
        new_team = winner + [new_member]
        team_key = frozenset(new_team)
        if team_key in state.seen:
            continue
        clf = tune_clf(X[:, new_team], y, estimator, grid_params)
        score_C = clf.best_score_
        params_C = clf.best_params_

        _log(f"new_team: {new_team},   score_C: {score_C}")
        state.seen.add(team_key)

        if score_C > score_best_i:
            score_best_i = score_C
            temp_winner = new_team
            best_params_i = params_C
            _log("****update ")

    if not temp_winner:
        _log("adding on top won't improve cv score")
        return 0, [], 0
    else:
        winner = temp_winner
        return score_best_i, winner, best_params_i


def SFFS_backward(X, y, idx, estimator, grid_params, state: _MsffsState):
    winner = state.winner_list[idx]
    update = 1
    never_updated = 1

    while update == 1:
        update = 0
        for drop_player in winner:
            new_team = winner.copy()
            new_team.remove(drop_player)
            team_key = frozenset(new_team)
            if team_key in state.seen:
                continue

            clf = tune_clf(X[:, new_team], y, estimator, grid_params)
            score_C = clf.best_score_
            params_C = clf.best_params_

            _log(f"backward_team: {new_team},  score_C: {score_C}")
            state.seen.add(team_key)

            if score_C > state.best_scores[len(new_team)]:
                state.best_scores[len(new_team)] = score_C
                state.winner_list[len(new_team)] = new_team
                state.best_params_list[len(new_team)] = params_C

                temp_winner = new_team
                update = 1
                never_updated = 0
                _log("****backward update")

        if update == 1:
            winner = temp_winner
    if never_updated == 1:
        return 0
    else:
        return len(winner)


def msffs_run(
    X: np.ndarray,
    y: np.ndarray,
    max_f: int,
    estimator: Any,
    grid_params: dict[str, Any] | Mapping[str, Any],
) -> dict[str, Any]:
    state = _MsffsState(
        seen=set(),
        best_scores=np.zeros(max_f + 1),
        winner_list=[[] for _ in range(max_f + 1)],
        best_params_list=[None for _ in range(max_f + 1)],
    )

    i = 1
    while i <= max_f:
        _log(f"Current No.features: {i}")
        s_best, selectf, param_best_i = mSFFS_forward(
            X, y, estimator, grid_params, state.winner_list[i - 1], state.best_scores[i], state
        )

        if s_best == 0:
            i += 1
            continue
        else:
            state.best_scores[i] = s_best
            state.winner_list[i] = selectf
            state.best_params_list[i] = param_best_i

            if i > 2:
                i_new = SFFS_backward(X, y, i, estimator, grid_params, state)
                if i_new > 0:
                    i = i_new

        i += 1

        _log(f"best_scores: {state.best_scores.tolist()}")
        _log(f"winner_list: {state.winner_list}")
        _log(f"best_params_list: {state.best_params_list}")

    return {
        "best_scores": state.best_scores,
        "winner_list": state.winner_list,
        "best_params_list": state.best_params_list,
    }
