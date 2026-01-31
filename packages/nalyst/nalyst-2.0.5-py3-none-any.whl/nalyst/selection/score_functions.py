"""
Score functions for feature selection.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
from scipy import stats


def chi2(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute chi-squared stats between each non-negative feature and class.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Sample vectors.
    y : ndarray of shape (n_samples,)
        Target vector (class labels).

    Returns
    -------
    chi2 : ndarray of shape (n_features,)
        Chi-squared statistics.
    p_values : ndarray of shape (n_features,)
        P-values.
    """
    X = np.atleast_2d(X)
    y = np.asarray(y)

    classes = np.unique(y)
    n_classes = len(classes)
    n_features = X.shape[1]

    chi2_stats = np.zeros(n_features)
    p_values = np.zeros(n_features)

    for j in range(n_features):
        # Build contingency table
        observed = np.zeros((n_classes, 2))

        for i, c in enumerate(classes):
            mask = y == c
            observed[i, 0] = np.sum(X[mask, j] > 0)
            observed[i, 1] = np.sum(X[mask, j] == 0)

        # Chi-squared test
        if observed.sum() > 0:
            chi2_stat, p_val, _, _ = stats.chi2_contingency(
                observed + 1e-10, correction=False
            )
            chi2_stats[j] = chi2_stat
            p_values[j] = p_val

    return chi2_stats, p_values


def f_classif(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute ANOVA F-value for the provided sample.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Sample vectors.
    y : ndarray of shape (n_samples,)
        Target vector.

    Returns
    -------
    f_statistic : ndarray of shape (n_features,)
        F-statistics.
    p_values : ndarray of shape (n_features,)
        P-values.
    """
    X = np.atleast_2d(X)
    y = np.asarray(y)

    classes = np.unique(y)
    n_features = X.shape[1]
    n_samples = X.shape[0]
    n_classes = len(classes)

    f_stats = np.zeros(n_features)
    p_values = np.zeros(n_features)

    for j in range(n_features):
        # Group by class
        groups = [X[y == c, j] for c in classes]

        # Overall mean
        overall_mean = np.mean(X[:, j])

        # Between-group variance
        ss_between = 0
        for g in groups:
            ss_between += len(g) * (np.mean(g) - overall_mean) ** 2

        # Within-group variance
        ss_within = 0
        for g in groups:
            ss_within += np.sum((g - np.mean(g)) ** 2)

        # Degrees of freedom
        df_between = n_classes - 1
        df_within = n_samples - n_classes

        if df_within > 0 and ss_within > 0:
            f_stats[j] = (ss_between / df_between) / (ss_within / df_within)
            p_values[j] = stats.f.sf(f_stats[j], df_between, df_within)
        else:
            f_stats[j] = 0
            p_values[j] = 1.0

    return f_stats, p_values


def f_regression(X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Univariate linear regression tests.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Sample vectors.
    y : ndarray of shape (n_samples,)
        Target vector.

    Returns
    -------
    f_statistic : ndarray of shape (n_features,)
        F-statistics.
    p_values : ndarray of shape (n_features,)
        P-values.
    """
    X = np.atleast_2d(X)
    y = np.asarray(y)

    n_samples, n_features = X.shape

    # Center the data
    X = X - np.mean(X, axis=0)
    y = y - np.mean(y)

    # Correlation coefficient
    correlation = np.dot(y, X) / np.sqrt(np.sum(X ** 2, axis=0) * np.sum(y ** 2) + 1e-10)

    # F-statistic
    df = n_samples - 2
    f_stats = correlation ** 2 / (1 - correlation ** 2 + 1e-10) * df

    # P-values
    p_values = stats.f.sf(f_stats, 1, df)

    return f_stats, p_values


def mutual_info_classif(
    X: np.ndarray,
    y: np.ndarray,
    *,
    discrete_features: str = "auto",
    n_neighbors: int = 3,
    random_state: int = None,
) -> np.ndarray:
    """
    Estimate mutual information for a discrete target variable.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Feature matrix.
    y : ndarray of shape (n_samples,)
        Target vector.
    discrete_features : str, default="auto"
        How to handle discrete features.
    n_neighbors : int, default=3
        Number of neighbors for MI estimation.
    random_state : int, optional
        Random seed.

    Returns
    -------
    mi : ndarray of shape (n_features,)
        Estimated mutual information.
    """
    X = np.atleast_2d(X)
    y = np.asarray(y)
    n_features = X.shape[1]

    mi = np.zeros(n_features)

    for j in range(n_features):
        mi[j] = _mutual_info_classification_single(X[:, j], y)

    return mi


def _mutual_info_classification_single(x: np.ndarray, y: np.ndarray) -> float:
    """Compute MI between single feature and discrete target."""
    # Use histogram-based estimation
    classes = np.unique(y)
    n_samples = len(y)

    # Discretize x if continuous
    n_bins = min(10, len(np.unique(x)))
    x_binned = np.digitize(x, bins=np.linspace(x.min(), x.max(), n_bins))

    # Joint and marginal probabilities
    x_vals = np.unique(x_binned)

    mi = 0
    for xi in x_vals:
        for yi in classes:
            p_xy = np.mean((x_binned == xi) & (y == yi))
            p_x = np.mean(x_binned == xi)
            p_y = np.mean(y == yi)

            if p_xy > 0 and p_x > 0 and p_y > 0:
                mi += p_xy * np.log(p_xy / (p_x * p_y))

    return max(0, mi)


def mutual_info_regression(
    X: np.ndarray,
    y: np.ndarray,
    *,
    discrete_features: str = "auto",
    n_neighbors: int = 3,
    random_state: int = None,
) -> np.ndarray:
    """
    Estimate mutual information for a continuous target variable.

    Parameters
    ----------
    X : ndarray of shape (n_samples, n_features)
        Feature matrix.
    y : ndarray of shape (n_samples,)
        Target vector.
    discrete_features : str, default="auto"
        How to handle discrete features.
    n_neighbors : int, default=3
        Number of neighbors for MI estimation.
    random_state : int, optional
        Random seed.

    Returns
    -------
    mi : ndarray of shape (n_features,)
        Estimated mutual information.
    """
    X = np.atleast_2d(X)
    y = np.asarray(y)
    n_features = X.shape[1]

    mi = np.zeros(n_features)

    for j in range(n_features):
        mi[j] = _mutual_info_regression_single(X[:, j], y, n_neighbors)

    return mi


def _mutual_info_regression_single(
    x: np.ndarray, y: np.ndarray, n_neighbors: int
) -> float:
    """Compute MI between two continuous variables using KNN estimation."""
    from scipy.special import digamma
    from scipy.spatial.distance import cdist

    n = len(x)
    x = x.reshape(-1, 1)
    y = y.reshape(-1, 1)
    xy = np.hstack([x, y])

    # Find k-th neighbor distances
    distances_xy = cdist(xy, xy)
    np.fill_diagonal(distances_xy, np.inf)

    # Get k-th nearest neighbor distance for each point
    k = min(n_neighbors, n - 1)
    epsilon = np.partition(distances_xy, k, axis=1)[:, k]

    # Count points within epsilon for x and y separately
    distances_x = cdist(x, x)
    distances_y = cdist(y, y)

    n_x = np.sum(distances_x < epsilon[:, np.newaxis], axis=1)
    n_y = np.sum(distances_y < epsilon[:, np.newaxis], axis=1)

    # MI estimation
    mi = digamma(n) + digamma(k) - np.mean(digamma(n_x + 1) + digamma(n_y + 1))

    return max(0, mi)
