# CV Reality Check 🛡️

Tiny, Kaggle-first toolkit that pressure-tests your cross-validation scheme against the hidden LB distribution. Drop it into a notebook, get a CV Reliability Score (0–100), drift/leakage diagnostics, and a ready-to-share markdown report.

## Why
- Public LB lies. CV leakage and train→test shift cost medals.
- Fast sanity layer before you hit `kaggle submit`.

## What you get
- **OOF audit**: fold scores + stability.
- **Adversarial validation**: train vs test separability.
- **Feature drift**: Wasserstein (numeric) / freq L1 (categorical).
- **Leakage radar**: ID-like columns, single-feature overfit, time-ish names.
- **Reliability score**: 0–100 with component breakdown + recommendations.
- **Reports**: `cv_report.md` + `cv_details.json` (CI-friendly).

## Quickstart (Kaggle notebook)
```python
!pip install -q cv-reality-check

import pandas as pd
from cvguard import check_cv

train = pd.read_csv('/kaggle/input/comp/train.csv')
test = pd.read_csv('/kaggle/input/comp/test.csv')

report = check_cv(
    train_df=train,
    test_df=test,
    target_col='target',
    cv_strategy='auto',   # or kfold|stratified|group|time
    metric='roc_auc',
    output_dir='cv_guard_report',
    verbose=True,
)
print('Reliability Score:', report.reliability.score)
```

## CLI (optional)
```bash
python -m cvguard.api --train train.csv --test test.csv --target target --metric roc_auc
```

## Notes
- Works for binary, multiclass, and regression.
- LightGBM if available; falls back to sklearn RF/GB for speed.
- Designed to stay under typical Kaggle CPU/memory budgets (sampling guards inside adversarial validation).

## Testing
```
pip install -e .[full]
pytest -q
```

Happy blending ✨
