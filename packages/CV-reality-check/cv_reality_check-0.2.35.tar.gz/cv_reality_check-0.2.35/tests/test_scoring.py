from cvguard.config import CVStats, DriftFeature, DriftResult, LeakageResult
from cvguard.scoring import compute_cv_reliability_score


def test_score_high_vs_low():
    good_stats = CVStats(oof_pred=[], fold_scores=[0.8, 0.82, 0.78], mean_score=0.8, std_score=0.02)
    bad_stats = CVStats(oof_pred=[], fold_scores=[0.1, 0.9, 0.2], mean_score=0.4, std_score=0.35)

    no_shift = DriftResult(features=[DriftFeature("f1", 0.1, "numeric"), DriftFeature("f2", 0.0, "categorical")])
    heavy_shift = DriftResult(features=[DriftFeature("f1", 0.9, "numeric"), DriftFeature("f2", 0.95, "categorical")])

    clean_leakage = LeakageResult(warnings=[])
    dirty_leakage = LeakageResult(warnings=["x"], has_strong_leakage=True)

    good_score = compute_cv_reliability_score(good_stats, adv_auc=0.55, drift_result=no_shift, leakage_result=clean_leakage)
    bad_score = compute_cv_reliability_score(bad_stats, adv_auc=0.95, drift_result=heavy_shift, leakage_result=dirty_leakage)

    assert good_score.score > bad_score.score
