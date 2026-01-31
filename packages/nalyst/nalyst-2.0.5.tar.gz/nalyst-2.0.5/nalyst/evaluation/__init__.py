"""
Model evaluation and selection for Nalyst.

This module provides tools for model assessment,
cross-validation, and hyperparameter tuning.
"""

from nalyst.evaluation.splitting import (
    train_test_split,
    KFold,
    StratifiedKFold,
    LeaveOneOut,
    ShuffleSplit,
)
from nalyst.evaluation.validation import (
    cross_val_score,
    cross_validate,
)
from nalyst.evaluation.search import (
    GridSearchCV,
    RandomizedSearchCV,
)

__all__ = [
    # Splitting
    "train_test_split",
    "KFold",
    "StratifiedKFold",
    "LeaveOneOut",
    "ShuffleSplit",
    # Validation
    "cross_val_score",
    "cross_validate",
    # Search
    "GridSearchCV",
    "RandomizedSearchCV",
]
