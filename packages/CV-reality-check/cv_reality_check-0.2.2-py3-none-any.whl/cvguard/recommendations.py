from __future__ import annotations

from typing import List

from .config import (
    CVConfig,
    CVReliabilityScore,
    DataConfig,
    DriftResult,
    LeakageResult,
    Recommendations,
)


def build_recommendations(
    data_cfg: DataConfig,
    current_cv: CVConfig,
    reliability: CVReliabilityScore,
    drift_result: DriftResult,
    leakage_result: LeakageResult,
) -> Recommendations:
    actions: List[str] = []

    score = reliability.score

    # 1. Общая оценка
    if score >= 80:
        actions.append(
            "CV appears reasonably reliable (score >= 80). Monitor LB but major changes are not required."
        )
    elif score >= 60:
        actions.append(
            "CV is moderately reliable (60 <= score < 80). Consider improving split strategy and reviewing shifted features."
        )
    else:
        actions.append(
            "CV is at high risk of misalignment with LB (score < 60). You should revise CV strategy and feature set."
        )

    # 2. Рекомендации по CV-стратегии
    recommended_cv = current_cv

    if data_cfg.time_col and current_cv.strategy not in ("time",):
        actions.append(
            f"Detected time column '{data_cfg.time_col}'. Consider using time-based CV instead of random splits."
        )
        recommended_cv = CVConfig(strategy="time", n_splits=current_cv.n_splits)

    elif data_cfg.group_col and current_cv.strategy not in ("group",):
        actions.append(
            f"Detected group column '{data_cfg.group_col}'. Consider using GroupKFold to avoid leakage across groups."
        )
        recommended_cv = CVConfig(strategy="group", n_splits=current_cv.n_splits)

    # 3. Drift-driven рекомендации
    strong_shift_features = [
        f.feature for f in drift_result.features if f.shift_score >= 0.7
    ]
    if strong_shift_features:
        actions.append(
            "Strong train-test shift detected in features: "
            + ", ".join(strong_shift_features[:10])
            + ". Consider dropping or robustly transforming them, "
              "or stratifying CV by one of these features."
        )

    # 4. Leakage-driven рекомендации
    if leakage_result.has_strong_leakage:
        actions.append(
            "Potential strong leakage detected. Review features mentioned in leakage warnings and consider removing or redesigning them."
        )
    if leakage_result.has_id_leakage:
        actions.append(
            "ID-like features appear to have high predictive power. Ensure they are not causing leakage (e.g., row identifiers or keys)."
        )
    if leakage_result.has_time_leakage:
        actions.append(
            "Features suggesting time leakage detected (e.g., 'future_', 'post_'). Check they don't use future information."
        )

    return Recommendations(
        recommended_cv=recommended_cv,
        actions=actions,
    )
