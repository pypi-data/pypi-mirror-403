import pandas as pd
from sklearn.datasets import make_classification

from cvguard.api import check_cv


def test_check_cv_end_to_end(tmp_path):
    X, y = make_classification(n_samples=120, n_features=6, n_informative=4, random_state=0)
    cols = [f"f{i}" for i in range(X.shape[1])]
    train_df = pd.DataFrame(X, columns=cols)
    train_df["target"] = y
    test_df = train_df.drop(columns=["target"]).sample(frac=0.5, random_state=1).reset_index(drop=True)

    report = check_cv(train_df=train_df, test_df=test_df, target_col="target", output_dir=tmp_path, verbose=False)

    assert report.reliability.score >= 0.0
    assert (tmp_path / "cv_report.md").exists()
    assert (tmp_path / "cv_details.json").exists()
