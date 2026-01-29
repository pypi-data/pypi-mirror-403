from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from .config import AdvValidationResult, DataConfig

try:
    from lightgbm import LGBMClassifier  # type: ignore
    _HAS_LGBM = True
except Exception:  # pragma: no cover - fallback path
    _HAS_LGBM = False


def _build_adv_model(random_state: int):
    if _HAS_LGBM:
        return LGBMClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=-1,
            random_state=random_state,
        )
    return RandomForestClassifier(
        n_estimators=150,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced",
    )


def adversarial_validation(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    data_cfg: DataConfig,
    random_state: int = 42,
    test_size: float = 0.3,
    max_rows: int = 200_000,
) -> AdvValidationResult:
    """Train a classifier to separate train vs test rows and return AUC + importances."""
    if len(train_df) == 0 or len(test_df) == 0:
        empty_df = pd.DataFrame({"feature": data_cfg.feature_cols, "importance": 0.0})
        return AdvValidationResult(adv_auc=0.5, feature_importances=empty_df)

    train_sample = train_df[data_cfg.feature_cols].copy()
    test_sample = test_df[data_cfg.feature_cols].copy()

    if len(train_sample) > max_rows:
        train_sample = train_sample.sample(max_rows, random_state=random_state)
    if len(test_sample) > max_rows:
        test_sample = test_sample.sample(max_rows, random_state=random_state)

    X_adv = pd.concat([train_sample, test_sample], axis=0, ignore_index=True)
    y_adv = np.concatenate(
        [np.zeros(len(train_sample), dtype=int), np.ones(len(test_sample), dtype=int)]
    )

    # Drop columns that are entirely NaN to avoid model crashes
    non_nan_cols = [c for c in X_adv.columns if not X_adv[c].isna().all()]
    X_adv = X_adv[non_nan_cols]

    if X_adv.shape[1] == 0:
        empty_df = pd.DataFrame({"feature": data_cfg.feature_cols, "importance": 0.0})
        return AdvValidationResult(adv_auc=0.5, feature_importances=empty_df)

    X_tr, X_val, y_tr, y_val = train_test_split(
        X_adv, y_adv, test_size=test_size, random_state=random_state, stratify=y_adv
    )

    clf = _build_adv_model(random_state)
    try:
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict_proba(X_val)[:, 1]
        adv_auc = float(roc_auc_score(y_val, y_pred))
    except Exception:
        adv_auc = 0.5

    # Feature importances handling
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        coef = getattr(clf, "coef_")
        importances = np.abs(coef).ravel()
    else:
        importances = np.zeros(X_adv.shape[1])

    # Align importances back to full feature list, filling missing columns with zero
    fi_df = pd.DataFrame({"feature": X_adv.columns, "importance": importances})
    fi_df = fi_df.sort_values("importance", ascending=False)

    missing_cols = [c for c in data_cfg.feature_cols if c not in fi_df["feature"].tolist()]
    if missing_cols:
        fi_df = pd.concat(
            [fi_df, pd.DataFrame({"feature": missing_cols, "importance": 0.0})],
            ignore_index=True,
        )

    return AdvValidationResult(adv_auc=float(adv_auc), feature_importances=fi_df)
