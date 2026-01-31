"""
Statistical tests for survival analysis.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List, Tuple
import numpy as np
from scipy.stats import chi2


def logrank_test(
    durations_A: np.ndarray,
    durations_B: np.ndarray,
    event_observed_A: Optional[np.ndarray] = None,
    event_observed_B: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Log-rank test for comparing two survival curves.

    Tests the null hypothesis that two groups have identical survival.

    Parameters
    ----------
    durations_A : ndarray
        Durations for group A.
    durations_B : ndarray
        Durations for group B.
    event_observed_A : ndarray, optional
        Event indicators for group A.
    event_observed_B : ndarray, optional
        Event indicators for group B.

    Returns
    -------
    result : dict
        Contains 'test_statistic', 'p_value', 'observed', 'expected'.

    Examples
    --------
    >>> from nalyst.survival import logrank_test
    >>> result = logrank_test(durations_A, durations_B, events_A, events_B)
    >>> print(f"p-value: {result['p_value']:.4f}")
    """
    durations_A = np.asarray(durations_A).flatten()
    durations_B = np.asarray(durations_B).flatten()

    if event_observed_A is None:
        event_observed_A = np.ones(len(durations_A), dtype=int)
    else:
        event_observed_A = np.asarray(event_observed_A).flatten().astype(int)

    if event_observed_B is None:
        event_observed_B = np.ones(len(durations_B), dtype=int)
    else:
        event_observed_B = np.asarray(event_observed_B).flatten().astype(int)

    # Combine data
    all_durations = np.concatenate([durations_A, durations_B])
    all_events = np.concatenate([event_observed_A, event_observed_B])
    group = np.concatenate([np.zeros(len(durations_A)), np.ones(len(durations_B))])

    # Unique event times
    unique_times = np.unique(all_durations[all_events == 1])

    O_A = 0  # Observed events in A
    E_A = 0  # Expected events in A
    V = 0    # Variance

    for t in unique_times:
        # At risk at time t
        at_risk_A = np.sum(durations_A >= t)
        at_risk_B = np.sum(durations_B >= t)
        at_risk = at_risk_A + at_risk_B

        # Events at time t
        events_A_t = np.sum((durations_A == t) & (event_observed_A == 1))
        events_B_t = np.sum((durations_B == t) & (event_observed_B == 1))
        events_t = events_A_t + events_B_t

        if at_risk > 1:
            # Expected events in A
            e_A = at_risk_A * events_t / at_risk

            # Hypergeometric variance
            v = (at_risk_A * at_risk_B * events_t * (at_risk - events_t)) / \
                (at_risk ** 2 * (at_risk - 1))

            O_A += events_A_t
            E_A += e_A
            V += v

    # Test statistic
    if V > 0:
        test_statistic = (O_A - E_A) ** 2 / V
        p_value = 1 - chi2.cdf(test_statistic, df=1)
    else:
        test_statistic = 0
        p_value = 1.0

    return {
        'test_statistic': test_statistic,
        'p_value': p_value,
        'observed_A': O_A,
        'expected_A': E_A,
        'observed_B': np.sum(event_observed_B) - O_A + O_A,  # Computed differently
        'variance': V,
    }


def wilcoxon_test(
    durations_A: np.ndarray,
    durations_B: np.ndarray,
    event_observed_A: Optional[np.ndarray] = None,
    event_observed_B: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Wilcoxon (Gehan-Breslow) test for comparing survival curves.

    Gives more weight to early events compared to log-rank test.

    Parameters
    ----------
    durations_A, durations_B : ndarray
        Durations for each group.
    event_observed_A, event_observed_B : ndarray, optional
        Event indicators.

    Returns
    -------
    result : dict
        Test results.
    """
    durations_A = np.asarray(durations_A).flatten()
    durations_B = np.asarray(durations_B).flatten()

    if event_observed_A is None:
        event_observed_A = np.ones(len(durations_A), dtype=int)
    else:
        event_observed_A = np.asarray(event_observed_A).flatten().astype(int)

    if event_observed_B is None:
        event_observed_B = np.ones(len(durations_B), dtype=int)
    else:
        event_observed_B = np.asarray(event_observed_B).flatten().astype(int)

    # Combine data
    all_durations = np.concatenate([durations_A, durations_B])
    all_events = np.concatenate([event_observed_A, event_observed_B])

    unique_times = np.unique(all_durations[all_events == 1])

    O_A = 0
    E_A = 0
    V = 0

    for t in unique_times:
        # At risk at time t (Wilcoxon weights by at-risk count)
        at_risk_A = np.sum(durations_A >= t)
        at_risk_B = np.sum(durations_B >= t)
        at_risk = at_risk_A + at_risk_B

        # Wilcoxon weight = number at risk
        w = at_risk

        events_A_t = np.sum((durations_A == t) & (event_observed_A == 1))
        events_B_t = np.sum((durations_B == t) & (event_observed_B == 1))
        events_t = events_A_t + events_B_t

        if at_risk > 1:
            e_A = at_risk_A * events_t / at_risk

            v = (at_risk_A * at_risk_B * events_t * (at_risk - events_t)) / \
                (at_risk ** 2 * (at_risk - 1))

            O_A += w * events_A_t
            E_A += w * e_A
            V += w ** 2 * v

    if V > 0:
        test_statistic = (O_A - E_A) ** 2 / V
        p_value = 1 - chi2.cdf(test_statistic, df=1)
    else:
        test_statistic = 0
        p_value = 1.0

    return {
        'test_statistic': test_statistic,
        'p_value': p_value,
        'test_name': 'Wilcoxon (Gehan-Breslow)',
    }


def tarone_ware_test(
    durations_A: np.ndarray,
    durations_B: np.ndarray,
    event_observed_A: Optional[np.ndarray] = None,
    event_observed_B: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Tarone-Ware test for comparing survival curves.

    Uses sqrt(at-risk) as weight, intermediate between log-rank and Wilcoxon.

    Parameters
    ----------
    durations_A, durations_B : ndarray
        Durations for each group.
    event_observed_A, event_observed_B : ndarray, optional
        Event indicators.

    Returns
    -------
    result : dict
        Test results.
    """
    durations_A = np.asarray(durations_A).flatten()
    durations_B = np.asarray(durations_B).flatten()

    if event_observed_A is None:
        event_observed_A = np.ones(len(durations_A), dtype=int)
    else:
        event_observed_A = np.asarray(event_observed_A).flatten().astype(int)

    if event_observed_B is None:
        event_observed_B = np.ones(len(durations_B), dtype=int)
    else:
        event_observed_B = np.asarray(event_observed_B).flatten().astype(int)

    all_durations = np.concatenate([durations_A, durations_B])
    all_events = np.concatenate([event_observed_A, event_observed_B])

    unique_times = np.unique(all_durations[all_events == 1])

    O_A = 0
    E_A = 0
    V = 0

    for t in unique_times:
        at_risk_A = np.sum(durations_A >= t)
        at_risk_B = np.sum(durations_B >= t)
        at_risk = at_risk_A + at_risk_B

        # Tarone-Ware weight = sqrt(at_risk)
        w = np.sqrt(at_risk)

        events_A_t = np.sum((durations_A == t) & (event_observed_A == 1))
        events_t = np.sum((all_durations == t) & (all_events == 1))

        if at_risk > 1:
            e_A = at_risk_A * events_t / at_risk

            v = (at_risk_A * at_risk_B * events_t * (at_risk - events_t)) / \
                (at_risk ** 2 * (at_risk - 1))

            O_A += w * events_A_t
            E_A += w * e_A
            V += w ** 2 * v

    if V > 0:
        test_statistic = (O_A - E_A) ** 2 / V
        p_value = 1 - chi2.cdf(test_statistic, df=1)
    else:
        test_statistic = 0
        p_value = 1.0

    return {
        'test_statistic': test_statistic,
        'p_value': p_value,
        'test_name': 'Tarone-Ware',
    }


def multivariate_logrank_test(
    durations: np.ndarray,
    groups: np.ndarray,
    event_observed: Optional[np.ndarray] = None,
) -> Dict[str, float]:
    """
    Log-rank test for multiple groups.

    Parameters
    ----------
    durations : ndarray
        Durations for all samples.
    groups : ndarray
        Group labels.
    event_observed : ndarray, optional
        Event indicators.

    Returns
    -------
    result : dict
        Test results.
    """
    durations = np.asarray(durations).flatten()
    groups = np.asarray(groups).flatten()

    if event_observed is None:
        event_observed = np.ones(len(durations), dtype=int)
    else:
        event_observed = np.asarray(event_observed).flatten().astype(int)

    unique_groups = np.unique(groups)
    n_groups = len(unique_groups)

    unique_times = np.unique(durations[event_observed == 1])

    # Observed and expected for each group
    O = np.zeros(n_groups)
    E = np.zeros(n_groups)
    V = np.zeros((n_groups, n_groups))

    for t in unique_times:
        # At risk in each group
        at_risk = np.array([np.sum((durations >= t) & (groups == g)) for g in unique_groups])
        total_at_risk = np.sum(at_risk)

        # Events in each group
        events = np.array([
            np.sum((durations == t) & (event_observed == 1) & (groups == g))
            for g in unique_groups
        ])
        total_events = np.sum(events)

        if total_at_risk > 1 and total_events > 0:
            # Expected events
            e = at_risk * total_events / total_at_risk
            O += events
            E += e

            # Variance-covariance
            factor = total_events * (total_at_risk - total_events) / \
                    (total_at_risk ** 2 * (total_at_risk - 1))

            for i in range(n_groups):
                for j in range(n_groups):
                    if i == j:
                        V[i, j] += factor * at_risk[i] * (total_at_risk - at_risk[i])
                    else:
                        V[i, j] -= factor * at_risk[i] * at_risk[j]

    # Test statistic (drop one group for degrees of freedom)
    O_reduced = O[:-1] - E[:-1]
    V_reduced = V[:-1, :-1]

    try:
        V_inv = np.linalg.inv(V_reduced + 1e-10 * np.eye(n_groups - 1))
        test_statistic = O_reduced @ V_inv @ O_reduced
        p_value = 1 - chi2.cdf(test_statistic, df=n_groups - 1)
    except np.linalg.LinAlgError:
        test_statistic = 0
        p_value = 1.0

    return {
        'test_statistic': test_statistic,
        'p_value': p_value,
        'degrees_of_freedom': n_groups - 1,
        'observed': O,
        'expected': E,
    }
