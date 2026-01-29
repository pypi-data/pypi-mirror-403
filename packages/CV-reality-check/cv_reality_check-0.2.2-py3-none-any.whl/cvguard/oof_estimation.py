from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from .config import CVConfig, CVStats, DataConfig, ProblemType


def _build_model(problem_type: ProblemType, n_classes: int | None, random_state: int = 42, base_model: str = "auto"):
    """Return a lightweight model with predict_proba/predict depending on task.

    Prefers LightGBM if available; falls back to sklearn RandomForest for reliability.
    """
    if base_model not in {"auto", "lgbm", "sklearn"}:
        raise ValueError("base_model must be one of {'auto','lgbm','sklearn'}")

    use_lgbm = base_model in {"auto", "lgbm"}
    if use_lgbm:
        try:
            from lightgbm import LGBMClassifier, LGBMRegressor

            if problem_type == ProblemType.REGRESSION:
                return LGBMRegressor(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=-1,
                    random_state=random_state,
                )
            elif problem_type == ProblemType.MULTICLASS:
                return LGBMClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=-1,
                    random_state=random_state,
                    objective="multiclass",
                    num_class=n_classes,
                )
            else:
                return LGBMClassifier(
                    n_estimators=200,
                    learning_rate=0.05,
                    max_depth=-1,
                    random_state=random_state,
                )
        except Exception:
            # fall back to sklearn
            pass

    if problem_type == ProblemType.REGRESSION:
        return RandomForestRegressor(n_estimators=150, random_state=random_state)
    else:
        return RandomForestClassifier(
            n_estimators=200,
            random_state=random_state,
            class_weight="balanced" if problem_type == ProblemType.BINARY else None,
        )


def _constant_prediction(y_val, y_train, problem_type: ProblemType, n_classes: int):
    """Provide safe constant predictions when a fold has a single class."""
    if problem_type == ProblemType.REGRESSION:
        return np.full_like(y_val, fill_value=float(np.mean(y_train)), dtype=float)
    if problem_type == ProblemType.BINARY:
        p = float(np.mean(y_train))
        return np.full_like(y_val, fill_value=p, dtype=float)
    # multiclass: uniform distribution over observed classes
    probs = np.zeros((len(y_val), n_classes), dtype=float)
    observed_class = int(y_train[0]) if len(y_train) else 0
    probs[:, observed_class] = 1.0
    return probs


def compute_oof_predictions(
    train_df: pd.DataFrame,
    data_cfg: DataConfig,
    cv_config: CVConfig,
    cv_splits: Iterable[Tuple[np.ndarray, np.ndarray]],
    metric_fn,
    base_model: str = "auto",
) -> CVStats:
    X = train_df[data_cfg.feature_cols].copy()

    # Safety: encode non-numeric columns to categorical codes so downstream models don't crash
    for col in data_cfg.categorical_cols:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = pd.Categorical(X[col]).codes
    for col in data_cfg.feature_cols:
        if not pd.api.types.is_numeric_dtype(X[col]):
            X[col] = pd.Categorical(X[col]).codes

    y = train_df[data_cfg.target_col].values

    n_samples = len(train_df)
    unique_classes = np.unique(y) if data_cfg.problem_type != ProblemType.REGRESSION else []
    n_classes = len(unique_classes) if data_cfg.problem_type == ProblemType.MULTICLASS else 0

    if data_cfg.problem_type == ProblemType.MULTICLASS:
        oof_pred = np.zeros((n_samples, n_classes), dtype=float)
    else:
        oof_pred = np.zeros(n_samples, dtype=float)

    fold_scores = []

    for fold, (train_idx, val_idx) in enumerate(cv_splits):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]

        if data_cfg.problem_type != ProblemType.REGRESSION and len(np.unique(y_train)) < 2:
            y_pred = _constant_prediction(y_val, y_train, data_cfg.problem_type, max(n_classes, 2))
            score = 0.0
        else:
            model = _build_model(
                data_cfg.problem_type,
                n_classes=n_classes if n_classes else None,
                random_state=cv_config.random_state + fold,
                base_model=base_model,
            )
            model.fit(X_train, y_train)

            if data_cfg.problem_type == ProblemType.REGRESSION:
                y_pred = model.predict(X_val)
            else:
                proba = model.predict_proba(X_val)
                if data_cfg.problem_type == ProblemType.BINARY:
                    # proba shape (n,2)
                    y_pred = proba[:, 1] if proba.shape[1] > 1 else proba[:, 0]
                else:
                    y_pred = proba
            try:
                score = metric_fn(y_val, y_pred)
            except Exception:
                score = 0.0

        oof_pred[val_idx] = y_pred
        fold_scores.append(float(score))

    # replace any NaNs in oof_pred with safer defaults
    if np.isnan(oof_pred).any():
        if oof_pred.ndim == 1:
            oof_pred = np.nan_to_num(oof_pred, nan=np.nanmean(oof_pred))
        else:
            oof_pred = np.nan_to_num(oof_pred, nan=1.0 / max(n_classes, 1))

    mean_score = float(np.nanmean(fold_scores))
    std_score = float(np.nanstd(fold_scores))

    return CVStats(
        oof_pred=oof_pred,
        fold_scores=fold_scores,
        mean_score=mean_score,
        std_score=std_score,
    )
