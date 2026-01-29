import numpy as np
import pandas as pd

from cvguard.data_utils import build_data_config
from cvguard.adv_validation import adversarial_validation


def test_adv_validation_detects_shift():
    rng = np.random.default_rng(0)
    train_df = pd.DataFrame({
        "f1": rng.normal(0, 1, 200),
        "f2": rng.normal(0, 1, 200),
        "target": rng.integers(0, 2, 200),
    })
    test_df = pd.DataFrame({
        "f1": rng.normal(3, 1, 200),
        "f2": rng.normal(3, 1, 200),
    })

    cfg = build_data_config(train_df, test_df, target_col="target")
    res = adversarial_validation(train_df, test_df, cfg, random_state=0)

    assert res.adv_auc > 0.8
