import pandas as pd
import numpy as np

from cvguard.data_utils import infer_problem_type, build_data_config
from cvguard.config import ProblemType


def test_infer_problem_type_binary():
    y = pd.Series([0, 1, 0, 1])
    assert infer_problem_type(y) == ProblemType.BINARY


def test_infer_problem_type_multiclass():
    y = pd.Series([0, 1, 2, 1, 0])
    assert infer_problem_type(y) == ProblemType.MULTICLASS


def test_infer_problem_type_regression():
    y = pd.Series([0.1, 0.2, 0.3, 0.4])
    assert infer_problem_type(y) == ProblemType.REGRESSION


def test_build_data_config_auto_ids():
    train_df = pd.DataFrame({
        "target": [0, 1, 0, 1],
        "num1": [1.0, 2.0, 3.0, 4.0],
        "cat1": ["a", "b", "a", "b"],
        "row_id": [1, 2, 3, 4],
    })
    test_df = train_df.drop(columns=["target"])

    cfg = build_data_config(train_df, test_df, target_col="target")

    assert cfg.problem_type == ProblemType.BINARY
    assert "num1" in cfg.numeric_cols
    assert "cat1" in cfg.categorical_cols
    assert "row_id" in cfg.id_cols
    assert "row_id" not in cfg.numeric_cols
