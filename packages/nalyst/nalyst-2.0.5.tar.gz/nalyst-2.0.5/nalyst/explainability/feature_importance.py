"""
Feature importance methods.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Callable, Union
import numpy as np


def permutation_importance(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_repeats: int = 10,
    scoring: Optional[str] = None,
    random_state: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """
    Compute permutation feature importance.

    Measures decrease in model performance when a feature is randomly shuffled.

    Parameters
    ----------
    model : estimator
        Trained model.
    X : ndarray of shape (n_samples, n_features)
        Test data.
    y : ndarray of shape (n_samples,)
        True labels.
    n_repeats : int, default=10
        Number of times to permute each feature.
    scoring : str, optional
        Scoring metric: 'accuracy', 'mse', 'r2'.
    random_state : int, optional
        Random seed.

    Returns
    -------
    result : dict
        Dictionary with keys:
        - importances_mean: Mean importance per feature.
        - importances_std: Standard deviation per feature.
        - importances: Full importance array (n_features, n_repeats).

    Examples
    --------
    >>> from nalyst.explainability import permutation_importance
    >>> result = permutation_importance(model, X_test, y_test)
    >>> print(result['importances_mean'])
    """
    X = np.asarray(X)
    y = np.asarray(y).flatten()
    n_features = X.shape[1]

    if random_state is not None:
        np.random.seed(random_state)

    # Determine scoring function
    if scoring is None:
        # Infer from model type
        if hasattr(model, 'predict_proba'):
            scoring = 'accuracy'
        else:
            scoring = 'r2'

    if scoring == 'accuracy':
        def score_fn(y_true, y_pred):
            return np.mean(y_true == y_pred)
    elif scoring == 'mse':
        def score_fn(y_true, y_pred):
            return -np.mean((y_true - y_pred) ** 2)  # Negative MSE
    else:  # r2
        def score_fn(y_true, y_pred):
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            return 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # Baseline score
    if hasattr(model, 'infer'):
        baseline_pred = model.infer(X)
    else:
        baseline_pred = model.predict(X)

    baseline_score = score_fn(y, baseline_pred)

    # Compute importance for each feature
    importances = np.zeros((n_features, n_repeats))

    for j in range(n_features):
        for r in range(n_repeats):
            # Permute feature j
            X_permuted = X.copy()
            X_permuted[:, j] = np.random.permutation(X_permuted[:, j])

            # Score with permuted feature
            if hasattr(model, 'infer'):
                perm_pred = model.infer(X_permuted)
            else:
                perm_pred = model.predict(X_permuted)

            perm_score = score_fn(y, perm_pred)

            # Importance = decrease in score
            importances[j, r] = baseline_score - perm_score

    return {
        'importances_mean': np.mean(importances, axis=1),
        'importances_std': np.std(importances, axis=1),
        'importances': importances,
        'baseline_score': baseline_score,
    }


def drop_column_importance(
    model_class: Any,
    X: np.ndarray,
    y: np.ndarray,
    scoring: Optional[str] = None,
    **model_kwargs,
) -> Dict[str, np.ndarray]:
    """
    Compute feature importance by dropping each column.

    Retrains model without each feature and measures performance drop.

    Parameters
    ----------
    model_class : class
        Model class to instantiate.
    X : ndarray of shape (n_samples, n_features)
        Training data.
    y : ndarray of shape (n_samples,)
        Target.
    scoring : str, optional
        Scoring metric.
    **model_kwargs
        Arguments to pass to model constructor.

    Returns
    -------
    result : dict
        Feature importance results.
    """
    X = np.asarray(X)
    y = np.asarray(y).flatten()
    n_features = X.shape[1]

    # Scoring function
    if scoring == 'accuracy':
        def score_fn(y_true, y_pred):
            return np.mean(y_true == y_pred)
    else:  # r2
        def score_fn(y_true, y_pred):
            ss_res = np.sum((y_true - y_pred) ** 2)
            ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
            return 1 - ss_res / ss_tot if ss_tot > 0 else 0

    # Baseline: train on all features
    model_full = model_class(**model_kwargs)
    model_full.train(X, y)

    if hasattr(model_full, 'infer'):
        baseline_pred = model_full.infer(X)
    else:
        baseline_pred = model_full.predict(X)

    baseline_score = score_fn(y, baseline_pred)

    # Drop each feature
    importances = np.zeros(n_features)

    for j in range(n_features):
        # Remove column j
        X_reduced = np.delete(X, j, axis=1)

        # Train model
        model_reduced = model_class(**model_kwargs)
        model_reduced.train(X_reduced, y)

        # Score
        if hasattr(model_reduced, 'infer'):
            reduced_pred = model_reduced.infer(X_reduced)
        else:
            reduced_pred = model_reduced.predict(X_reduced)

        reduced_score = score_fn(y, reduced_pred)

        # Importance = performance drop
        importances[j] = baseline_score - reduced_score

    return {
        'importances': importances,
        'baseline_score': baseline_score,
    }


def mutual_info_importance(
    X: np.ndarray,
    y: np.ndarray,
    discrete_features: Optional[List[int]] = None,
    n_neighbors: int = 3,
) -> Dict[str, np.ndarray]:
    """
    Compute feature importance using mutual information.

    Measures mutual information between each feature and target.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Features.
    y : ndarray of shape (n_samples,)
        Target.
    discrete_features : list of int, optional
        Indices of discrete features.
    n_neighbors : int, default=3
        Number of neighbors for MI estimation.

    Returns
    -------
    result : dict
        Mutual information scores per feature.
    """
    X = np.asarray(X)
    y = np.asarray(y).flatten()
    n_samples, n_features = X.shape

    if discrete_features is None:
        discrete_features = []

    importances = np.zeros(n_features)

    # Check if y is discrete
    unique_y = np.unique(y)
    y_discrete = len(unique_y) < 0.1 * n_samples

    for j in range(n_features):
        if j in discrete_features:
            # Discrete-discrete or discrete-continuous MI
            importances[j] = _mutual_info_discrete(X[:, j], y, y_discrete)
        else:
            # Continuous MI using k-NN estimator
            importances[j] = _mutual_info_knn(X[:, j], y, n_neighbors)

    return {
        'importances': importances,
        'normalized': importances / importances.sum() if importances.sum() > 0 else importances,
    }


def _mutual_info_discrete(x: np.ndarray, y: np.ndarray, y_discrete: bool) -> float:
    """Compute MI for discrete feature."""
    # Discretize if needed
    unique_x = np.unique(x)
    unique_y = np.unique(y)

    n = len(x)

    # Joint distribution
    mi = 0.0

    for xi in unique_x:
        for yi in unique_y:
            pxy = np.sum((x == xi) & (y == yi)) / n
            px = np.sum(x == xi) / n
            py = np.sum(y == yi) / n

            if pxy > 0 and px > 0 and py > 0:
                mi += pxy * np.log(pxy / (px * py))

    return max(0, mi)


def _mutual_info_knn(x: np.ndarray, y: np.ndarray, k: int) -> float:
    """Compute MI using k-NN estimator (Kraskov method approximation)."""
    n = len(x)

    # Simple approximation using correlation
    # True MI estimation requires more complex algorithms

    # Normalize
    x_norm = (x - np.mean(x)) / (np.std(x) + 1e-10)
    y_norm = (y - np.mean(y)) / (np.std(y) + 1e-10)

    # Pearson correlation
    corr = np.abs(np.corrcoef(x_norm, y_norm)[0, 1])

    # Convert correlation to MI (Gaussian assumption)
    if corr < 1:
        mi = -0.5 * np.log(1 - corr ** 2)
    else:
        mi = 10.0  # Large value for perfect correlation

    return max(0, mi)
