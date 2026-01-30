import numpy as np
import pandas as pd

from cvguard.cv_schemes import build_cv
from cvguard.config import DataConfig, CVConfig, ProblemType


def _dummy_data_config(problem_type=ProblemType.BINARY):
    return DataConfig(
        target_col="target",
        feature_cols=["f1"],
        numeric_cols=["f1"],
        categorical_cols=[],
        id_cols=[],
        time_col=None,
        group_col=None,
        problem_type=problem_type,
    )


def test_stratified_splits_no_overlap():
    y = np.array([0, 1] * 25)
    data_cfg = _dummy_data_config()
    cv_cfg = CVConfig(strategy="stratified", n_splits=5, shuffle=True, random_state=42)

    for train_idx, val_idx in build_cv(data_cfg, cv_cfg, y=y, groups=None):
        assert len(set(train_idx) & set(val_idx)) == 0


def test_time_split_respects_order():
    y = np.arange(20)
    data_cfg = _dummy_data_config()
    data_cfg.time_col = "time"
    cv_cfg = CVConfig(strategy="time", n_splits=4)

    for train_idx, val_idx in build_cv(data_cfg, cv_cfg, y=y, groups=None):
        assert train_idx.max() < val_idx.min()


def test_group_split_uses_groups():
    y = np.array([0, 1, 0, 1])
    groups = np.array([1, 1, 2, 2])
    data_cfg = _dummy_data_config()
    data_cfg.group_col = "grp"
    cv_cfg = CVConfig(strategy="group", n_splits=2)

    splits = list(build_cv(data_cfg, cv_cfg, y=y, groups=groups))
    assert len(splits) == 2
    for train_idx, val_idx in splits:
        assert set(groups[train_idx]) & set(groups[val_idx]) == set()
