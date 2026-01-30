from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import DataConfig, ProblemType


def infer_problem_type(y: pd.Series) -> ProblemType:
    y_no_nan = y.dropna()
    if y_no_nan.empty:
        return ProblemType.REGRESSION

    if pd.api.types.is_numeric_dtype(y_no_nan):
        unique_vals = np.unique(y_no_nan)
        n_unique = len(unique_vals)
        if n_unique <= 2:
            return ProblemType.BINARY
        if pd.api.types.is_integer_dtype(y_no_nan) and n_unique <= 20:
            return ProblemType.MULTICLASS
        if n_unique <= 20 and np.all(np.isclose(unique_vals, np.round(unique_vals))):
            return ProblemType.MULTICLASS
        return ProblemType.REGRESSION

    n_unique = y_no_nan.nunique(dropna=True)
    if n_unique <= 2:
        return ProblemType.BINARY
    return ProblemType.MULTICLASS


def split_feature_types(
    df: pd.DataFrame,
    target_col: str,
    id_cols: List[str] | None = None,
    auto_id_threshold: float = 0.95,
) -> Tuple[List[str], List[str], List[str]]:
    if df.dropna(how="all").empty:
        raise ValueError("Dataset contains only NaN rows")

    id_cols = list(id_cols or [])
    feature_cols = [c for c in df.columns if c not in [target_col] + id_cols]

    numeric_cols: List[str] = []
    categorical_cols: List[str] = []

    n_rows = len(df)
    for col in feature_cols:
        col_series = df[col]
        if col_series.isna().all():
            continue

        unique_ratio = col_series.nunique(dropna=True) / max(n_rows, 1)
        name_has_id = "id" in col.lower()

        if pd.api.types.is_numeric_dtype(col_series):
            numeric_cols.append(col)
            is_int_like = pd.api.types.is_integer_dtype(col_series) or name_has_id
            if unique_ratio >= auto_id_threshold and is_int_like and col not in id_cols:
                id_cols.append(col)
        else:
            categorical_cols.append(col)
            if unique_ratio >= auto_id_threshold and col not in id_cols:
                id_cols.append(col)

    numeric_cols = [c for c in numeric_cols if c not in id_cols]
    categorical_cols = [c for c in categorical_cols if c not in id_cols]

    return numeric_cols, categorical_cols, id_cols


def encode_categoricals(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    data_cfg: DataConfig,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Encode object/categorical columns into integer codes consistently across train/test.

    - Uses combined categories from train+test to avoid unseen-category crashes.
    - NaNs become code -1.
    - Returns copies of dataframes with encoded columns; other columns are unchanged.
    """
    train_enc = train_df.copy()
    test_enc = test_df.copy()

    for col in data_cfg.categorical_cols:
        combined = pd.concat([train_df[col], test_df[col]], axis=0)
        categories = pd.Categorical(combined).categories
        train_enc[col] = pd.Categorical(train_df[col], categories=categories).codes
        test_enc[col] = pd.Categorical(test_df[col], categories=categories).codes
    return train_enc, test_enc


def build_data_config(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    id_cols: List[str] | None = None,
    time_col: str | None = None,
    group_col: str | None = None,
) -> DataConfig:
    if target_col not in train_df.columns:
        raise ValueError(f"target_col '{target_col}' not found in train_df")

    y = train_df[target_col]
    p_type = infer_problem_type(y)

    numeric_cols, categorical_cols, id_cols_ = split_feature_types(
        train_df, target_col=target_col, id_cols=id_cols
    )

    feature_cols = numeric_cols + categorical_cols + id_cols_

    return DataConfig(
        target_col=target_col,
        feature_cols=feature_cols,
        numeric_cols=numeric_cols,
        categorical_cols=categorical_cols,
        id_cols=id_cols_,
        time_col=time_col,
        group_col=group_col,
        problem_type=p_type,
        n_rows_train=len(train_df),
        n_rows_test=len(test_df),
    )
