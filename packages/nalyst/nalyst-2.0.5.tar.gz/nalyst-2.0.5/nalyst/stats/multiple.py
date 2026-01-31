"""
Multiple testing correction methods.
"""

from __future__ import annotations

from typing import Tuple, List
import numpy as np


def bonferroni(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Bonferroni correction for multiple comparisons.

    Controls family-wise error rate (FWER).

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired significance level.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values.

    Examples
    --------
    >>> from nalyst.stats import bonferroni
    >>> pvals = [0.01, 0.04, 0.03, 0.005]
    >>> reject, corrected = bonferroni(pvals)
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    pvalues_corrected = np.minimum(pvalues * n, 1.0)
    reject = pvalues_corrected <= alpha

    return reject, pvalues_corrected


def holm(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Holm-Bonferroni step-down correction.

    Controls FWER with more power than Bonferroni.

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired significance level.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values.

    Examples
    --------
    >>> from nalyst.stats import holm
    >>> reject, corrected = holm([0.01, 0.04, 0.03, 0.005])
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    # Sort indices
    sorted_idx = np.argsort(pvalues)
    sorted_pvals = pvalues[sorted_idx]

    # Corrected p-values
    corrected = np.zeros(n)

    for i in range(n):
        corrected[i] = sorted_pvals[i] * (n - i)

    # Enforce monotonicity
    corrected = np.maximum.accumulate(corrected)
    corrected = np.minimum(corrected, 1.0)

    # Unsort
    pvalues_corrected = np.empty(n)
    pvalues_corrected[sorted_idx] = corrected

    reject = pvalues_corrected <= alpha

    return reject, pvalues_corrected


def benjamini_hochberg(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Benjamini-Hochberg procedure for FDR control.

    Controls false discovery rate (FDR).

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired FDR level.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values (q-values).

    Examples
    --------
    >>> from nalyst.stats import benjamini_hochberg
    >>> reject, qvalues = benjamini_hochberg([0.01, 0.04, 0.03, 0.005])
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    # Sort indices
    sorted_idx = np.argsort(pvalues)
    sorted_pvals = pvalues[sorted_idx]

    # Corrected p-values (q-values)
    corrected = np.zeros(n)

    for i in range(n):
        corrected[i] = sorted_pvals[i] * n / (i + 1)

    # Enforce monotonicity (backwards)
    corrected = np.minimum.accumulate(corrected[::-1])[::-1]
    corrected = np.minimum(corrected, 1.0)

    # Unsort
    pvalues_corrected = np.empty(n)
    pvalues_corrected[sorted_idx] = corrected

    # Reject if corrected p-value <= alpha
    reject = pvalues_corrected <= alpha

    return reject, pvalues_corrected


def fdr_correction(
    pvalues: np.ndarray,
    alpha: float = 0.05,
    method: str = 'bh',
) -> Tuple[np.ndarray, np.ndarray]:
    """
    FDR correction using various methods.

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired FDR level.
    method : str, default='bh'
        Method: 'bh' (Benjamini-Hochberg), 'by' (Benjamini-Yekutieli),
        'fdr_bh', 'fdr_by'.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values.

    Examples
    --------
    >>> from nalyst.stats import fdr_correction
    >>> reject, qvalues = fdr_correction(pvalues, method='bh')
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    if method in ['bh', 'fdr_bh']:
        return benjamini_hochberg(pvalues, alpha)

    elif method in ['by', 'fdr_by']:
        # Benjamini-Yekutieli (for dependent tests)
        sorted_idx = np.argsort(pvalues)
        sorted_pvals = pvalues[sorted_idx]

        # Correction factor for dependence
        cm = np.sum(1.0 / np.arange(1, n + 1))

        corrected = np.zeros(n)
        for i in range(n):
            corrected[i] = sorted_pvals[i] * n * cm / (i + 1)

        corrected = np.minimum.accumulate(corrected[::-1])[::-1]
        corrected = np.minimum(corrected, 1.0)

        pvalues_corrected = np.empty(n)
        pvalues_corrected[sorted_idx] = corrected

        reject = pvalues_corrected <= alpha

        return reject, pvalues_corrected

    else:
        raise ValueError(f"Unknown method: {method}")


def sidak(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    idk correction for multiple comparisons.

    Slightly less conservative than Bonferroni for independent tests.

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired significance level.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values.
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    # idk correction
    pvalues_corrected = 1 - (1 - pvalues) ** n
    reject = pvalues_corrected <= alpha

    return reject, pvalues_corrected


def hochberg(pvalues: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Hochberg step-up procedure.

    Controls FWER, assumes independence or positive dependence.

    Parameters
    ----------
    pvalues : ndarray
        Original p-values.
    alpha : float, default=0.05
        Desired significance level.

    Returns
    -------
    reject : ndarray of bool
        True for hypotheses to reject.
    pvalues_corrected : ndarray
        Corrected p-values.
    """
    pvalues = np.asarray(pvalues)
    n = len(pvalues)

    # Sort indices (descending)
    sorted_idx = np.argsort(pvalues)[::-1]
    sorted_pvals = pvalues[sorted_idx]

    corrected = np.zeros(n)

    for i in range(n):
        corrected[i] = sorted_pvals[i] * (i + 1)

    # Enforce monotonicity
    corrected = np.minimum.accumulate(corrected)
    corrected = np.minimum(corrected, 1.0)

    # Unsort
    pvalues_corrected = np.empty(n)
    pvalues_corrected[sorted_idx] = corrected

    reject = pvalues_corrected <= alpha

    return reject, pvalues_corrected
