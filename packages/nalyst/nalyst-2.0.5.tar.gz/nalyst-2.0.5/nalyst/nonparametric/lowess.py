"""
LOWESS and LOESS smoothing.
"""

from __future__ import annotations

from typing import Optional, Tuple
import numpy as np


def lowess(
    x: np.ndarray,
    y: np.ndarray,
    frac: float = 0.6667,
    it: int = 3,
    delta: float = 0.0,
    x_out: Optional[np.ndarray] = None,
    return_sorted: bool = True,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Locally Weighted Scatterplot Smoothing (LOWESS).

    Robust local regression using weighted least squares.

    Parameters
    ----------
    x : ndarray of shape (n_samples,)
        Independent variable.
    y : ndarray of shape (n_samples,)
        Dependent variable.
    frac : float, default=0.6667
        Fraction of data used for each local fit.
    it : int, default=3
        Number of robustifying iterations.
    delta : float, default=0.0
        Distance within which to use linear interpolation.
    x_out : ndarray, optional
        Points at which to evaluate. If None, uses x.
    return_sorted : bool, default=True
        If True, return results sorted by x.

    Returns
    -------
    x_out : ndarray
        Sorted x values (if return_sorted).
    y_smooth : ndarray
        Smoothed y values.

    Examples
    --------
    >>> from nalyst.nonparametric import lowess
    >>> x_smooth, y_smooth = lowess(x, y, frac=0.3)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n = len(x)

    if x_out is None:
        x_out = x.copy()
    else:
        x_out = np.asarray(x_out).flatten()

    # Sort by x
    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]

    # Number of points in each window
    k = int(np.ceil(frac * n))
    k = max(2, min(k, n))

    # Initialize weights for robustifying
    robustness_weights = np.ones(n)

    y_smooth = np.zeros(len(x_out))

    for iteration in range(it + 1):
        for i, x0 in enumerate(x_out):
            # Find k nearest neighbors
            distances = np.abs(x_sorted - x0)
            sorted_dist_idx = np.argsort(distances)

            # Window of k points
            window_idx = sorted_dist_idx[:k]
            window_x = x_sorted[window_idx]
            window_y = y_sorted[window_idx]
            window_robust = robustness_weights[window_idx]

            # Tricube weights
            max_dist = np.max(distances[window_idx])
            if max_dist > 0:
                u = distances[window_idx] / (max_dist * 1.0001)
                tricube = (1 - u ** 3) ** 3
            else:
                tricube = np.ones(k)

            # Combined weights
            weights = tricube * window_robust

            # Weighted linear regression
            wx = weights * window_x
            wy = weights * window_y
            wxx = weights * window_x ** 2
            wxy = weights * window_x * window_y
            w = weights

            sum_w = np.sum(w)
            sum_wx = np.sum(wx)
            sum_wy = np.sum(wy)
            sum_wxx = np.sum(wxx)
            sum_wxy = np.sum(wxy)

            denom = sum_w * sum_wxx - sum_wx ** 2

            if np.abs(denom) > 1e-10:
                beta1 = (sum_w * sum_wxy - sum_wx * sum_wy) / denom
                beta0 = (sum_wy - beta1 * sum_wx) / sum_w
            else:
                beta0 = sum_wy / sum_w if sum_w > 0 else np.mean(window_y)
                beta1 = 0

            y_smooth[i] = beta0 + beta1 * x0

        # Robustifying (skip on last iteration)
        if iteration < it:
            # Residuals
            y_pred_all = np.zeros(n)
            for i in range(n):
                distances = np.abs(x_sorted - x_sorted[i])
                sorted_dist_idx = np.argsort(distances)
                window_idx = sorted_dist_idx[:k]

                window_x = x_sorted[window_idx]
                window_y = y_sorted[window_idx]
                window_robust = robustness_weights[window_idx]

                max_dist = np.max(distances[window_idx])
                if max_dist > 0:
                    u = distances[window_idx] / (max_dist * 1.0001)
                    tricube = (1 - u ** 3) ** 3
                else:
                    tricube = np.ones(k)

                weights = tricube * window_robust

                wx = weights * window_x
                wy = weights * window_y

                sum_w = np.sum(weights)
                sum_wx = np.sum(wx)
                sum_wy = np.sum(wy)
                sum_wxx = np.sum(weights * window_x ** 2)
                sum_wxy = np.sum(weights * window_x * window_y)

                denom = sum_w * sum_wxx - sum_wx ** 2

                if np.abs(denom) > 1e-10:
                    beta1 = (sum_w * sum_wxy - sum_wx * sum_wy) / denom
                    beta0 = (sum_wy - beta1 * sum_wx) / sum_w
                else:
                    beta0 = sum_wy / sum_w if sum_w > 0 else np.mean(window_y)
                    beta1 = 0

                y_pred_all[i] = beta0 + beta1 * x_sorted[i]

            residuals = np.abs(y_sorted - y_pred_all)
            median_residual = np.median(residuals)

            if median_residual > 0:
                u = residuals / (6 * median_residual)
                robustness_weights = np.where(u < 1, (1 - u ** 2) ** 2, 0)
            else:
                robustness_weights = np.ones(n)

    if return_sorted:
        out_sort_idx = np.argsort(x_out)
        return x_out[out_sort_idx], y_smooth[out_sort_idx]
    else:
        return x_out, y_smooth


def loess(
    x: np.ndarray,
    y: np.ndarray,
    frac: float = 0.6667,
    degree: int = 1,
    it: int = 3,
    x_out: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    LOESS (Local Polynomial Regression).

    Like LOWESS but with configurable polynomial degree.

    Parameters
    ----------
    x : ndarray
        Independent variable.
    y : ndarray
        Dependent variable.
    frac : float, default=0.6667
        Fraction of data for local fit.
    degree : int, default=1
        Polynomial degree (1=linear, 2=quadratic).
    it : int, default=3
        Robustifying iterations.
    x_out : ndarray, optional
        Evaluation points.

    Returns
    -------
    x_out : ndarray
        X values.
    y_smooth : ndarray
        Smoothed values.

    Examples
    --------
    >>> from nalyst.nonparametric import loess
    >>> x_smooth, y_smooth = loess(x, y, frac=0.3, degree=2)
    """
    x = np.asarray(x).flatten()
    y = np.asarray(y).flatten()

    n = len(x)

    if x_out is None:
        x_out = x.copy()
    else:
        x_out = np.asarray(x_out).flatten()

    sort_idx = np.argsort(x)
    x_sorted = x[sort_idx]
    y_sorted = y[sort_idx]

    k = int(np.ceil(frac * n))
    k = max(degree + 2, min(k, n))

    robustness_weights = np.ones(n)
    y_smooth = np.zeros(len(x_out))

    for iteration in range(it + 1):
        for i, x0 in enumerate(x_out):
            distances = np.abs(x_sorted - x0)
            sorted_dist_idx = np.argsort(distances)
            window_idx = sorted_dist_idx[:k]

            window_x = x_sorted[window_idx]
            window_y = y_sorted[window_idx]
            window_robust = robustness_weights[window_idx]

            max_dist = np.max(distances[window_idx])
            if max_dist > 0:
                u = distances[window_idx] / (max_dist * 1.0001)
                tricube = (1 - u ** 3) ** 3
            else:
                tricube = np.ones(k)

            weights = tricube * window_robust

            # Build polynomial design matrix
            dx = window_x - x0
            design = np.column_stack([dx ** p for p in range(degree + 1)])

            W = np.diag(weights)

            try:
                XtWX = design.T @ W @ design
                XtWy = design.T @ W @ window_y
                beta = np.linalg.solve(XtWX + 1e-10 * np.eye(degree + 1), XtWy)
                y_smooth[i] = beta[0]  # Intercept is prediction at x0
            except np.linalg.LinAlgError:
                y_smooth[i] = np.mean(window_y)

        if iteration < it:
            # Update robustness weights
            y_pred_all = np.zeros(n)

            for i in range(n):
                distances = np.abs(x_sorted - x_sorted[i])
                sorted_dist_idx = np.argsort(distances)
                window_idx = sorted_dist_idx[:k]

                window_x = x_sorted[window_idx]
                window_y = y_sorted[window_idx]

                max_dist = np.max(distances[window_idx])
                if max_dist > 0:
                    u = distances[window_idx] / (max_dist * 1.0001)
                    tricube = (1 - u ** 3) ** 3
                else:
                    tricube = np.ones(k)

                weights = tricube * robustness_weights[window_idx]

                dx = window_x - x_sorted[i]
                design = np.column_stack([dx ** p for p in range(degree + 1)])

                W = np.diag(weights)

                try:
                    XtWX = design.T @ W @ design
                    XtWy = design.T @ W @ window_y
                    beta = np.linalg.solve(XtWX + 1e-10 * np.eye(degree + 1), XtWy)
                    y_pred_all[i] = beta[0]
                except np.linalg.LinAlgError:
                    y_pred_all[i] = np.mean(window_y)

            residuals = np.abs(y_sorted - y_pred_all)
            median_residual = np.median(residuals)

            if median_residual > 0:
                u = residuals / (6 * median_residual)
                robustness_weights = np.where(u < 1, (1 - u ** 2) ** 2, 0)

    out_sort_idx = np.argsort(x_out)
    return x_out[out_sort_idx], y_smooth[out_sort_idx]
