"""
Calibration curve calculation.
"""

from __future__ import annotations

from typing import Tuple, Literal

import numpy as np


def calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    *,
    n_bins: int = 5,
    strategy: Literal["uniform", "quantile"] = "uniform",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute true and predicted probabilities for a calibration curve.

    Parameters
    ----------
    y_true : ndarray of shape (n_samples,)
        True targets.
    y_prob : ndarray of shape (n_samples,)
        Probabilities of the positive class.
    n_bins : int, default=5
        Number of bins to discretize the [0, 1] interval.
    strategy : {"uniform", "quantile"}, default="uniform"
        Strategy used to define the widths of the bins.

    Returns
    -------
    prob_true : ndarray of shape (n_bins,)
        The proportion of positive samples in each bin.
    prob_pred : ndarray of shape (n_bins,)
        The mean predicted probability in each bin.

    Examples
    --------
    >>> from nalyst.calibration import calibration_curve
    >>> y_true = np.array([0, 0, 0, 1, 1, 1])
    >>> y_prob = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    >>> prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=3)
    """
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)

    if strategy == "uniform":
        bins = np.linspace(0, 1, n_bins + 1)
    elif strategy == "quantile":
        quantiles = np.linspace(0, 1, n_bins + 1)
        bins = np.percentile(y_prob, quantiles * 100)
        bins = np.unique(bins)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Assign samples to bins
    bin_indices = np.digitize(y_prob, bins[1:-1])

    prob_true = []
    prob_pred = []

    for i in range(len(bins) - 1):
        mask = bin_indices == i
        if np.sum(mask) > 0:
            prob_true.append(np.mean(y_true[mask]))
            prob_pred.append(np.mean(y_prob[mask]))

    return np.array(prob_true), np.array(prob_pred)
