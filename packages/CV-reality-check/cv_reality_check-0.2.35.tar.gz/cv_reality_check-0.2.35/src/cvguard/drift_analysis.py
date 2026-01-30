from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from scipy.stats import wasserstein_distance

from .config import DataConfig, DriftFeature, DriftResult


def _numeric_shift_score(train_col: pd.Series, test_col: pd.Series) -> float:
    train_clean = train_col.dropna()
    test_clean = test_col.dropna()
    if len(train_clean) == 0 or len(test_clean) == 0:
        return 0.0
    if train_clean.nunique() == 1 and test_clean.nunique() == 1:
        if float(train_clean.iloc[0]) == float(test_clean.iloc[0]):
            return 0.0
    wdist = wasserstein_distance(train_clean, test_clean)
    q1, q3 = np.percentile(train_clean, [25, 75])
    iqr = max(q3 - q1, 1e-6)
    score = float(min(wdist / iqr, 5.0) / 5.0)
    return score


def _categorical_shift_score(train_col: pd.Series, test_col: pd.Series, top_k: int = 20) -> float:
    train_freq = train_col.value_counts(normalize=True)
    test_freq = test_col.value_counts(normalize=True)

    top_cats = train_freq.index[:top_k]
    score = 0.0
    for cat in top_cats:
        p_train = train_freq.get(cat, 0.0)
        p_test = test_freq.get(cat, 0.0)
        score += abs(p_train - p_test)
    score = float(min(score, 2.0) / 2.0)
    return score


def compute_feature_shift(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    data_cfg: DataConfig,
) -> DriftResult:
    drift_features: List[DriftFeature] = []

    for col in data_cfg.numeric_cols:
        if col not in test_df.columns:
            drift_features.append(
                DriftFeature(col, shift_score=1.0, feature_type="numeric", note="missing in test")
            )
            continue
        score = _numeric_shift_score(train_df[col], test_df[col])
        note = ""
        if score > 0.7:
            note = "strong numeric shift"
        elif score > 0.4:
            note = "moderate numeric shift"
        drift_features.append(DriftFeature(feature=col, shift_score=score, feature_type="numeric", note=note))

    for col in data_cfg.categorical_cols:
        if col not in test_df.columns:
            drift_features.append(
                DriftFeature(col, shift_score=1.0, feature_type="categorical", note="missing in test")
            )
            continue
        score = _categorical_shift_score(train_df[col], test_df[col])
        note = ""
        if score > 0.7:
            note = "strong category shift"
        elif score > 0.4:
            note = "moderate category shift"
        drift_features.append(DriftFeature(feature=col, shift_score=score, feature_type="categorical", note=note))

    return DriftResult(features=drift_features)
