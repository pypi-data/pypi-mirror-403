from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .config import DataConfig, LeakageResult, ProblemType

try:
    from lightgbm import LGBMClassifier, LGBMRegressor  # type: ignore
    _HAS_LGBM = True
except Exception:  # pragma: no cover
    _HAS_LGBM = False


def _encode_if_needed(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series
    return pd.Series(pd.Categorical(series).codes, index=series.index)


def _single_feature_score(
    train_df: pd.DataFrame,
    feature: str,
    target_col: str,
    problem_type: ProblemType,
) -> float:
    X_col = _encode_if_needed(train_df[feature])
    X = X_col.to_frame()
    y = train_df[target_col].values

    if X_col.nunique(dropna=True) <= 1:
        return 0.0

    if problem_type == ProblemType.REGRESSION:
        model = LGBMRegressor(n_estimators=60, learning_rate=0.1) if _HAS_LGBM else RandomForestRegressor(n_estimators=80)
        try:
            model.fit(X, y)
            pred = model.predict(X)
            y_mean = y.mean()
            ss_tot = np.sum((y - y_mean) ** 2)
            ss_res = np.sum((y - pred) ** 2)
            r2 = 1 - ss_res / (ss_tot + 1e-8)
            return float(r2)
        except Exception:
            return 0.0
    else:
        model = LGBMClassifier(n_estimators=60, learning_rate=0.1) if _HAS_LGBM else RandomForestClassifier(n_estimators=120)
        try:
            model.fit(X, y)
            proba = model.predict_proba(X)
            if proba.shape[1] == 1:
                return 0.5
            from sklearn.metrics import roc_auc_score

            if problem_type == ProblemType.BINARY:
                return float(roc_auc_score(y, proba[:, 1]))
            return float(roc_auc_score(y, proba, multi_class="ovr"))
        except Exception:
            return 0.5


def run_leakage_checks(
    train_df: pd.DataFrame,
    data_cfg: DataConfig,
    top_n_features: int = 30,
    strong_threshold: float = 0.98,
    id_cardinality_ratio: float = 0.9,
) -> LeakageResult:
    warnings: List[str] = []
    has_strong_leakage = False
    has_id_leakage = False
    has_time_leakage = False

    n_rows = len(train_df)

    for col in data_cfg.id_cols:
        unique_ratio = train_df[col].nunique(dropna=True) / max(n_rows, 1)
        if unique_ratio > id_cardinality_ratio:
            warnings.append(
                f"[ID] Column '{col}' looks like a row identifier (unique_ratio={unique_ratio:.3f})."
            )
            has_id_leakage = True

    candidate_features = [f for f in data_cfg.feature_cols if f not in data_cfg.id_cols]
    candidate_features = candidate_features[:top_n_features]

    for col in candidate_features:
        score = _single_feature_score(train_df, col, data_cfg.target_col, data_cfg.problem_type)
        if data_cfg.problem_type == ProblemType.REGRESSION:
            if score > strong_threshold:
                warnings.append(
                    f"[LEAKAGE] Feature '{col}' alone explains target too well (R2={score:.3f})."
                )
                has_strong_leakage = True
        else:
            if score > strong_threshold:
                warnings.append(
                    f"[LEAKAGE] Feature '{col}' alone predicts target too well (AUC={score:.3f})."
                )
                has_strong_leakage = True

    if data_cfg.time_col:
        for col in data_cfg.feature_cols:
            name = col.lower()
            if any(prefix in name for prefix in ["future_", "post_", "after_", "next_"]):
                warnings.append(
                    f"[TIME_LEAKAGE] Feature '{col}' name suggests it may use future information."
                )
                has_time_leakage = True

    return LeakageResult(
        warnings=warnings,
        has_strong_leakage=has_strong_leakage,
        has_id_leakage=has_id_leakage,
        has_time_leakage=has_time_leakage,
    )
