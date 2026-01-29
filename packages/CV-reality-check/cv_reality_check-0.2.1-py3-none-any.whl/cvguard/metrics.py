from __future__ import annotations

from typing import Callable

import numpy as np
from sklearn import metrics

from .config import ProblemType


class MetricNotSupported(ValueError):
    pass


def get_metric_fn(name: str, problem_type: ProblemType) -> Callable:
    """Return a callable metric (higher is better) for the given problem type."""
    name = name.lower()

    if name in ("roc_auc", "auc"):
        def metric_fn(y_true, y_pred):
            # Supports binary (1d proba) and multiclass (2d proba matrix)
            if y_pred.ndim == 1:
                return metrics.roc_auc_score(y_true, y_pred)
            return metrics.roc_auc_score(y_true, y_pred, multi_class="ovr")
        return metric_fn

    if name in ("average_precision", "ap"):
        def metric_fn(y_true, y_pred):
            if y_pred.ndim > 1:
                # micro-average for multiclass
                return metrics.average_precision_score(y_true, y_pred, average="micro")
            return metrics.average_precision_score(y_true, y_pred)
        return metric_fn

    if name in ("logloss", "log_loss"):
        def metric_fn(y_true, y_pred_proba):
            # sklearn handles binary / multiclass automatically
            return -metrics.log_loss(y_true, y_pred_proba)
        return metric_fn

    if name in ("rmse",):
        def metric_fn(y_true, y_pred):
            return -float(np.sqrt(metrics.mean_squared_error(y_true, y_pred)))
        return metric_fn

    if name in ("r2",):
        def metric_fn(y_true, y_pred):
            return metrics.r2_score(y_true, y_pred)
        return metric_fn

    if name in ("accuracy", "acc"):
        def metric_fn(y_true, y_pred):
            if y_pred.ndim > 1:
                y_pred_labels = np.argmax(y_pred, axis=1)
            else:
                y_pred_labels = (y_pred >= 0.5).astype(int)
            return metrics.accuracy_score(y_true, y_pred_labels)
        return metric_fn

    raise MetricNotSupported(f"Unknown or unsupported metric: {name}")
