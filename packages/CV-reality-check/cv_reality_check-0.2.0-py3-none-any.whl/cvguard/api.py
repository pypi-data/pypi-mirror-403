from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pandas as pd

from .adv_validation import adversarial_validation
from .config import CVConfig, CVReport
from .cv_schemes import build_cv
from .data_utils import build_data_config
from .drift_analysis import compute_feature_shift
from .leakage_checks import run_leakage_checks
from .metrics import get_metric_fn
from .oof_estimation import compute_oof_predictions
from .recommendations import build_recommendations
from .report_generator import generate_json_report, generate_markdown_report
from .scoring import compute_cv_reliability_score


def check_cv(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    target_col: str,
    cv_strategy: str = "auto",
    n_splits: int = 5,
    id_cols: Optional[list] = None,
    time_col: Optional[str] = None,
    group_col: Optional[str] = None,
    metric: str = "roc_auc",
    random_state: int = 42,
    output_dir: Optional[str] = None,
    verbose: bool = True,
    base_model: str = "auto",
) -> CVReport:
    """Run the full CV reliability pipeline."""
    output_path = Path(output_dir or "./cv_guard_report")

    if verbose:
        print("[cvguard] building data config…")
    data_cfg = build_data_config(
        train_df=train_df,
        test_df=test_df,
        target_col=target_col,
        id_cols=id_cols,
        time_col=time_col,
        group_col=group_col,
    )

    cv_cfg = CVConfig(
        strategy=cv_strategy,
        n_splits=n_splits,
        shuffle=True,
        random_state=random_state,
    )

    y = train_df[target_col].values
    groups = train_df[group_col].values if group_col and group_col in train_df.columns else None
    cv_splits = list(build_cv(data_cfg, cv_cfg, y=y, groups=groups))

    if verbose:
        print("[cvguard] computing OOF predictions…")
    metric_fn = get_metric_fn(metric, data_cfg.problem_type)
    cv_stats = compute_oof_predictions(
        train_df=train_df,
        data_cfg=data_cfg,
        cv_config=cv_cfg,
        cv_splits=cv_splits,
        metric_fn=metric_fn,
        base_model=base_model,
    )

    if verbose:
        print("[cvguard] running adversarial validation…")
    adv_result = adversarial_validation(
        train_df=train_df,
        test_df=test_df,
        data_cfg=data_cfg,
        random_state=random_state,
    )

    if verbose:
        print("[cvguard] measuring feature drift…")
    drift_result = compute_feature_shift(
        train_df=train_df,
        test_df=test_df,
        data_cfg=data_cfg,
    )

    if verbose:
        print("[cvguard] scanning leakage heuristics…")
    leakage_result = run_leakage_checks(
        train_df=train_df,
        data_cfg=data_cfg,
    )

    reliability = compute_cv_reliability_score(
        cv_stats=cv_stats,
        adv_auc=adv_result.adv_auc,
        drift_result=drift_result,
        leakage_result=leakage_result,
    )

    recommendations = build_recommendations(
        data_cfg=data_cfg,
        current_cv=cv_cfg,
        reliability=reliability,
        drift_result=drift_result,
        leakage_result=leakage_result,
    )

    report = CVReport(
        data_config=data_cfg,
        cv_config=cv_cfg,
        cv_stats=cv_stats,
        adv_result=adv_result,
        drift_result=drift_result,
        leakage_result=leakage_result,
        reliability=reliability,
        recommendations=recommendations,
    )

    if verbose:
        print(f"[cvguard] writing reports to {output_path.resolve()}")
    generate_markdown_report(report, output_path)
    generate_json_report(report, output_path)

    return report


def _cli():
    parser = argparse.ArgumentParser(description="Kaggle CV Guard")
    parser.add_argument("--train", required=True, help="Path to train.csv")
    parser.add_argument("--test", required=True, help="Path to test.csv")
    parser.add_argument("--target", required=True, help="Target column name")
    parser.add_argument("--metric", default="roc_auc")
    parser.add_argument("--cv", dest="cv_strategy", default="auto")
    parser.add_argument("--n-splits", dest="n_splits", type=int, default=5)
    parser.add_argument("--time-col", dest="time_col", default=None)
    parser.add_argument("--group-col", dest="group_col", default=None)
    parser.add_argument("--output", dest="output_dir", default="cv_guard_report")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress prints")

    args = parser.parse_args()

    train_df = pd.read_csv(args.train)
    test_df = pd.read_csv(args.test)

    check_cv(
        train_df=train_df,
        test_df=test_df,
        target_col=args.target,
        cv_strategy=args.cv_strategy,
        n_splits=args.n_splits,
        time_col=args.time_col,
        group_col=args.group_col,
        metric=args.metric,
        output_dir=args.output_dir,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    _cli()
