"""
Permutation importance.
"""

from __future__ import annotations

from typing import Optional, Callable

import numpy as np


def permutation_importance(
    estimator,
    X: np.ndarray,
    y: np.ndarray,
    *,
    scoring: Optional[Callable] = None,
    n_repeats: int = 5,
    n_jobs: Optional[int] = None,
    random_state: Optional[int] = None,
) -> dict:
    """
    Permutation importance for feature evaluation.

    Parameters
    ----------
    estimator : object
        Fitted estimator.
    X : ndarray of shape (n_samples, n_features)
        Data to compute importance on.
    y : ndarray of shape (n_samples,)
        Targets.
    scoring : callable, optional
        Scoring function. If None, uses estimator.score.
    n_repeats : int, default=5
        Number of times to permute each feature.
    n_jobs : int, optional
        Number of jobs (not implemented).
    random_state : int, optional
        Random seed.

    Returns
    -------
    result : dict
        Dictionary with keys:
        - importances_mean: Mean importance for each feature.
        - importances_std: Standard deviation.
        - importances: Full array of shape (n_features, n_repeats).

    Examples
    --------
    >>> from nalyst.inspection import permutation_importance
    >>> result = permutation_importance(model, X_test, y_test, n_repeats=10)
    >>> result["importances_mean"]
    """
    if random_state is not None:
        np.random.seed(random_state)

    X = np.asarray(X)
    y = np.asarray(y)
    n_samples, n_features = X.shape

    # Base score
    if scoring is not None:
        base_score = scoring(estimator, X, y)
    else:
        base_score = estimator.score(X, y)

    # Compute importance for each feature
    importances = np.zeros((n_features, n_repeats))

    for j in range(n_features):
        for r in range(n_repeats):
            # Permute feature j
            X_permuted = X.copy()
            X_permuted[:, j] = np.random.permutation(X_permuted[:, j])

            # Score with permuted feature
            if scoring is not None:
                permuted_score = scoring(estimator, X_permuted, y)
            else:
                permuted_score = estimator.score(X_permuted, y)

            # Importance is decrease in score
            importances[j, r] = base_score - permuted_score

    return {
        "importances_mean": np.mean(importances, axis=1),
        "importances_std": np.std(importances, axis=1),
        "importances": importances,
    }
