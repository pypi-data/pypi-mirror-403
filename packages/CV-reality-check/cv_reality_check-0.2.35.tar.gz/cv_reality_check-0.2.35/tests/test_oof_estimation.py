import numpy as np
import pandas as pd
from sklearn.datasets import make_classification

from cvguard.data_utils import build_data_config
from cvguard.cv_schemes import build_cv
from cvguard.config import CVConfig
from cvguard.metrics import get_metric_fn
from cvguard.oof_estimation import compute_oof_predictions


def _make_df(n_samples=120, n_classes=2, n_features=6, random_state=42):
    X, y = make_classification(
        n_samples=n_samples,
        n_features=n_features,
        n_informative=4,
        n_redundant=0,
        n_classes=n_classes,
        random_state=random_state,
    )
    cols = [f"f{i}" for i in range(n_features)]
    df = pd.DataFrame(X, columns=cols)
    df["target"] = y
    return df


def test_oof_binary_shapes_and_scores():
    train_df = _make_df(n_classes=2)
    test_df = train_df.drop(columns=["target"]).copy()

    data_cfg = build_data_config(train_df, test_df, target_col="target")
    cv_cfg = CVConfig(n_splits=3, shuffle=True, random_state=0)
    cv_splits = list(build_cv(data_cfg, cv_cfg, y=train_df["target"].values))
    metric_fn = get_metric_fn("roc_auc", data_cfg.problem_type)

    stats = compute_oof_predictions(train_df, data_cfg, cv_cfg, cv_splits, metric_fn)

    assert stats.oof_pred.shape[0] == len(train_df)
    assert np.isfinite(stats.mean_score)


def test_oof_multiclass_matrix():
    train_df = _make_df(n_classes=3, n_features=8, random_state=7)
    test_df = train_df.drop(columns=["target"]).copy()

    data_cfg = build_data_config(train_df, test_df, target_col="target")
    cv_cfg = CVConfig(n_splits=3, shuffle=True, random_state=0)
    cv_splits = list(build_cv(data_cfg, cv_cfg, y=train_df["target"].values))
    metric_fn = get_metric_fn("logloss", data_cfg.problem_type)

    stats = compute_oof_predictions(train_df, data_cfg, cv_cfg, cv_splits, metric_fn)

    assert stats.oof_pred.shape == (len(train_df), len(train_df["target"].unique()))
