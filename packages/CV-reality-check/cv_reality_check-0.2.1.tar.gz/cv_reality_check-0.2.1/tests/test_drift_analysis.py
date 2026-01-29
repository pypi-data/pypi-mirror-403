import pandas as pd

from cvguard.data_utils import build_data_config
from cvguard.drift_analysis import compute_feature_shift


def test_shift_scores_ordered():
    train_df = pd.DataFrame({
        "target": [0, 1, 0, 1, 0],
        "stable": [1, 1, 1, 1, 1],
        "shifted": [0, 0, 0, 0, 0],
    })
    test_df = pd.DataFrame({
        "stable": [1, 1, 1, 1, 1],
        "shifted": [5, 5, 5, 5, 5],
    })

    cfg = build_data_config(train_df, test_df, target_col="target")
    result = compute_feature_shift(train_df, test_df, cfg)

    scores = {f.feature: f.shift_score for f in result.features}
    assert scores["shifted"] > scores["stable"]
