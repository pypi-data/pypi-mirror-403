from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


class ProblemType(str, Enum):
    BINARY = "binary"
    MULTICLASS = "multiclass"
    REGRESSION = "regression"


@dataclass
class DataConfig:
    target_col: str
    feature_cols: List[str]
    numeric_cols: List[str]
    categorical_cols: List[str]
    id_cols: List[str] = field(default_factory=list)
    time_col: Optional[str] = None
    group_col: Optional[str] = None
    problem_type: ProblemType = ProblemType.BINARY
    n_rows_train: int = 0
    n_rows_test: int = 0


@dataclass
class CVConfig:
    strategy: str = "auto"  # auto | kfold | stratified | group | time
    n_splits: int = 5
    shuffle: bool = True
    random_state: int = 42


@dataclass
class CVStats:
    oof_pred: np.ndarray
    fold_scores: List[float]
    mean_score: float
    std_score: float


@dataclass
class AdvValidationResult:
    adv_auc: float
    feature_importances: pd.DataFrame  # columns: ["feature", "importance"]


@dataclass
class DriftFeature:
    feature: str
    shift_score: float
    feature_type: str
    note: str = ""


@dataclass
class DriftResult:
    features: List[DriftFeature]


@dataclass
class LeakageResult:
    warnings: List[str]
    has_strong_leakage: bool = False
    has_id_leakage: bool = False
    has_time_leakage: bool = False


@dataclass
class CVReliabilityScore:
    score: float  # 0..100
    components: Dict[str, float]  # e.g. {"cv_stability": 0.2, "shift": 0.4, ...}


@dataclass
class Recommendations:
    recommended_cv: CVConfig
    actions: List[str]


@dataclass
class CVReport:
    data_config: DataConfig
    cv_config: CVConfig
    cv_stats: CVStats
    adv_result: AdvValidationResult
    drift_result: DriftResult
    leakage_result: LeakageResult
    reliability: CVReliabilityScore
    recommendations: Recommendations
