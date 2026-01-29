from __future__ import annotations

import json
from pathlib import Path

from .config import CVReport


def generate_markdown_report(report: CVReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "cv_report.md"

    lines = []
    lines.append("# Kaggle CV Guard Report\n")

    lines.append("## Summary\n")
    lines.append(f"- CV Reliability Score: **{report.reliability.score:.1f} / 100**")
    lines.append(f"- Problem type: **{report.data_config.problem_type.value}**")
    lines.append(
        f"- Current CV strategy: **{report.cv_config.strategy}** (n_splits={report.cv_config.n_splits})"
    )
    lines.append("")

    lines.append("## Reliability Components\n")
    for k, v in report.reliability.components.items():
        lines.append(f"- {k}: {v:.3f}")
    lines.append("")

    lines.append("## CV Statistics\n")
    lines.append(f"- Mean CV score: **{report.cv_stats.mean_score:.4f}**")
    lines.append(f"- Std CV score: **{report.cv_stats.std_score:.4f}**")
    lines.append("- Fold scores: " + ", ".join(f"{s:.4f}" for s in report.cv_stats.fold_scores))
    lines.append("")

    lines.append("## Adversarial Validation\n")
    lines.append(f"- Adversarial AUC (train vs test): **{report.adv_result.adv_auc:.4f}**")
    top_fi = report.adv_result.feature_importances.head(10)
    lines.append("Top drift-driving features (by adversarial importance):")
    for _, row in top_fi.iterrows():
        lines.append(f"- {row['feature']}: importance={row['importance']}")
    lines.append("")

    lines.append("## Feature Shift\n")
    sorted_shift = sorted(report.drift_result.features, key=lambda f: f.shift_score, reverse=True)
    if sorted_shift:
        lines.append("Top shifted features:")
        for f in sorted_shift[:10]:
            lines.append(
                f"- {f.feature} ({f.feature_type}), shift_score={f.shift_score:.3f} {('[' + f.note + ']') if f.note else ''}"
            )
    else:
        lines.append("No features evaluated for shift.")
    lines.append("")

    lines.append("## Leakage Warnings\n")
    if report.leakage_result.warnings:
        for w in report.leakage_result.warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- No obvious leakage patterns detected.")
    lines.append("")

    lines.append("## Recommendations\n")
    for a in report.recommendations.actions:
        lines.append(f"- {a}")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_json_report(report: CVReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "cv_details.json"

    data = {
        "reliability": {
            "score": report.reliability.score,
            "components": report.reliability.components,
        },
        "cv": {
            "strategy": report.cv_config.strategy,
            "n_splits": report.cv_config.n_splits,
        },
        "cv_stats": {
            "mean_score": report.cv_stats.mean_score,
            "std_score": report.cv_stats.std_score,
            "fold_scores": report.cv_stats.fold_scores,
        },
        "adv_validation": {
            "adv_auc": report.adv_result.adv_auc,
            "top_features": report.adv_result.feature_importances.head(20).to_dict(orient="records"),
        },
        "drift": {
            "features": [
                {
                    "feature": f.feature,
                    "shift_score": f.shift_score,
                    "feature_type": f.feature_type,
                    "note": f.note,
                }
                for f in report.drift_result.features
            ]
        },
        "leakage": {
            "warnings": report.leakage_result.warnings,
            "has_leakage": report.leakage_result.has_strong_leakage
            or report.leakage_result.has_id_leakage
            or report.leakage_result.has_time_leakage,
        },
        "recommended_cv": {
            "strategy": report.recommendations.recommended_cv.strategy,
            "n_splits": report.recommendations.recommended_cv.n_splits,
        },
    }

    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path
