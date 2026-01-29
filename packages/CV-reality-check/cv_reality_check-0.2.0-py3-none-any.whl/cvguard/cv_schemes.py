from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
from sklearn.model_selection import (
    GroupKFold,
    KFold,
    StratifiedKFold,
    TimeSeriesSplit,
)

from .config import DataConfig, CVConfig, ProblemType


def _choose_strategy(data: DataConfig, cv_config: CVConfig, y) -> str:
    if cv_config.strategy != "auto":
        return cv_config.strategy
    if data.time_col:
        return "time"
    if data.group_col:
        return "group"
    if data.problem_type in (ProblemType.BINARY, ProblemType.MULTICLASS):
        return "stratified"
    return "kfold"


def build_cv(
    data: DataConfig,
    cv_config: CVConfig,
    y,
    groups=None,
) -> Iterable[Tuple[np.ndarray, np.ndarray]]:
    """Yield train/validation indices for the requested CV strategy."""
    strategy = _choose_strategy(data, cv_config, y)

    n_splits = max(2, cv_config.n_splits)
    shuffle = cv_config.shuffle
    random_state = cv_config.random_state

    if strategy == "time":
        # TimeSeriesSplit expects ordered data; disable shuffle
        tscv = TimeSeriesSplit(n_splits=n_splits)
        for train_idx, val_idx in tscv.split(np.arange(len(y))):
            yield train_idx, val_idx

    elif strategy == "group":
        if groups is None:
            raise ValueError("groups must be provided for group CV")
        n_groups = len(np.unique(groups))
        if n_groups < n_splits:
            n_splits = max(2, n_groups)
        gkf = GroupKFold(n_splits=n_splits)
        for train_idx, val_idx in gkf.split(X=np.zeros_like(y), y=y, groups=groups):
            yield train_idx, val_idx

    elif strategy == "stratified":
        # If stratification impossible (single class), fall back to KFold
        if len(np.unique(y)) < 2:
            kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
            for train_idx, val_idx in kf.split(X=np.zeros_like(y)):
                yield train_idx, val_idx
            return
        skf = StratifiedKFold(
            n_splits=n_splits, shuffle=shuffle, random_state=random_state
        )
        for train_idx, val_idx in skf.split(X=np.zeros_like(y), y=y):
            yield train_idx, val_idx

    elif strategy == "kfold":
        kf = KFold(n_splits=n_splits, shuffle=shuffle, random_state=random_state)
        for train_idx, val_idx in kf.split(X=np.zeros_like(y)):
            yield train_idx, val_idx

    else:
        raise ValueError(f"Unknown CV strategy: {strategy}")
