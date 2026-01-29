from __future__ import annotations

from typing import Dict

import numpy as np

from .config import CVReliabilityScore, CVStats, DriftResult, LeakageResult


def compute_cv_reliability_score(
    cv_stats: CVStats,
    adv_auc: float,
    drift_result: DriftResult,
    leakage_result: LeakageResult,
) -> CVReliabilityScore:
    """Aggregate diagnostics into a 0–100 reliability score."""
    mean_score = cv_stats.mean_score
    std_score = cv_stats.std_score

    if not np.isfinite(mean_score) or abs(mean_score) < 1e-8:
        cv_instability = 1.0
    else:
        cv_instability = float(np.clip(std_score / abs(mean_score), 0.0, 1.0))

    adv_shift = float(np.clip((adv_auc - 0.5) / 0.5, 0.0, 1.0))

    strong_shift_threshold = 0.7
    n_features = len(drift_result.features)
    if n_features == 0:
        shift_ratio = 0.0
    else:
        n_strong = sum(1 for f in drift_result.features if f.shift_score >= strong_shift_threshold)
        shift_ratio = float(np.clip(n_strong / n_features, 0.0, 1.0))

    leakage_penalty = 0.0
    if leakage_result.has_strong_leakage:
        leakage_penalty += 1.0
    if leakage_result.has_id_leakage:
        leakage_penalty += 0.5
    if leakage_result.has_time_leakage:
        leakage_penalty += 0.5
    leakage_penalty = float(np.clip(leakage_penalty / 2.0, 0.0, 1.0))

    w_cv = 0.3
    w_adv = 0.3
    w_shift = 0.2
    w_leak = 0.2

    risk = float(np.clip(w_cv * cv_instability + w_adv * adv_shift + w_shift * shift_ratio + w_leak * leakage_penalty, 0.0, 1.0))
    score = (1.0 - risk) * 100.0

    components: Dict[str, float] = {
        "cv_instability": cv_instability,
        "adv_shift": adv_shift,
        "feature_shift_ratio": shift_ratio,
        "leakage_penalty": leakage_penalty,
    }

    return CVReliabilityScore(score=score, components=components)
