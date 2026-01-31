"""
Kaplan-Meier estimator for survival analysis.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Tuple, List
import numpy as np


class KaplanMeierFitter:
    """
    Kaplan-Meier survival function estimator.

    Non-parametric estimator of the survival function from
    right-censored data.

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level for confidence intervals.

    Attributes
    ----------
    survival_function_ : ndarray
        Estimated survival probabilities.
    timeline_ : ndarray
        Time points.
    event_table_ : dict
        Event counts at each time.
    median_survival_time_ : float
        Median survival time.
    confidence_interval_ : tuple
        Upper and lower CI bounds.

    Examples
    --------
    >>> from nalyst.survival import KaplanMeierFitter
    >>> kmf = KaplanMeierFitter()
    >>> kmf.fit(durations, event_observed)
    >>> print(kmf.median_survival_time_)
    """

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
        label: Optional[str] = None,
    ) -> "KaplanMeierFitter":
        """
        Fit the Kaplan-Meier estimator.

        Parameters
        ----------
        durations : ndarray of shape (n_samples,)
            Observed durations (time to event or censoring).
        event_observed : ndarray of shape (n_samples,), optional
            1 if event occurred, 0 if censored. Default: all events.
        label : str, optional
            Label for this fit.

        Returns
        -------
        self
        """
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        self.label_ = label or "KM_estimate"

        # Sort by time
        sorted_idx = np.argsort(durations)
        times = durations[sorted_idx]
        events = event_observed[sorted_idx]

        # Get unique event times
        unique_times = np.unique(times[events == 1])

        # Build event table
        n_samples = len(times)
        n_at_risk = n_samples

        timeline = [0.0]
        survival = [1.0]
        variance = [0.0]

        event_table = {
            'time': [],
            'at_risk': [],
            'events': [],
            'censored': [],
        }

        for t in unique_times:
            # Count events and censored at this time
            at_t = times == t
            d = np.sum(events[at_t])  # Deaths

            # At risk just before t
            at_risk = np.sum(times >= t)

            if at_risk > 0:
                # Kaplan-Meier estimate
                s = survival[-1] * (1 - d / at_risk)

                # Greenwood's formula for variance
                if at_risk > d:
                    v = variance[-1] + d / (at_risk * (at_risk - d))
                else:
                    v = variance[-1]

                timeline.append(t)
                survival.append(s)
                variance.append(v)

                # Update at-risk
                censored_before = np.sum((times < t) & (times >= (timeline[-2] if len(timeline) > 1 else 0)) & (events == 0))

                event_table['time'].append(t)
                event_table['at_risk'].append(at_risk)
                event_table['events'].append(d)
                event_table['censored'].append(censored_before)

        self.timeline_ = np.array(timeline)
        self.survival_function_ = np.array(survival)
        self._variance = np.array(variance)
        self.event_table_ = event_table

        # Confidence intervals using log-log transformation
        from scipy.stats import norm
        z = norm.ppf(1 - self.alpha / 2)

        with np.errstate(divide='ignore', invalid='ignore'):
            log_s = np.log(self.survival_function_)
            log_s = np.where(np.isinf(log_s), -1e10, log_s)

            se = np.sqrt(self._variance)

            # Log-log CI
            lower = np.exp(log_s - z * se / np.abs(log_s + 1e-10))
            upper = np.exp(log_s + z * se / np.abs(log_s + 1e-10))

        self.confidence_interval_upper_ = np.clip(upper, 0, 1)
        self.confidence_interval_lower_ = np.clip(lower, 0, 1)

        # Median survival time
        self.median_survival_time_ = self._compute_median()

        return self

    def _compute_median(self) -> float:
        """Compute median survival time."""
        # Find first time where S(t) <= 0.5
        below_median = self.survival_function_ <= 0.5

        if np.any(below_median):
            idx = np.argmax(below_median)
            return self.timeline_[idx]
        else:
            return np.inf

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """
        Get survival function values at specified times.

        Parameters
        ----------
        times : ndarray
            Times at which to evaluate survival function.

        Returns
        -------
        survival : ndarray
            Survival probabilities.
        """
        times = np.asarray(times)

        # Step function interpolation
        result = np.ones_like(times, dtype=float)

        for i, t in enumerate(times):
            if t < self.timeline_[0]:
                result[i] = 1.0
            elif t >= self.timeline_[-1]:
                result[i] = self.survival_function_[-1]
            else:
                idx = np.searchsorted(self.timeline_, t, side='right') - 1
                result[i] = self.survival_function_[idx]

        return result

    def plot_data(self) -> Dict[str, np.ndarray]:
        """
        Get data for plotting the survival curve.

        Returns
        -------
        data : dict
            Contains 'timeline', 'survival', 'ci_lower', 'ci_upper'.
        """
        return {
            'timeline': self.timeline_,
            'survival': self.survival_function_,
            'ci_lower': self.confidence_interval_lower_,
            'ci_upper': self.confidence_interval_upper_,
            'label': self.label_,
        }

    def summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.

        Returns
        -------
        summary : dict
        """
        return {
            'median_survival_time': self.median_survival_time_,
            'n_events': sum(self.event_table_['events']),
            'n_at_risk_start': self.event_table_['at_risk'][0] if self.event_table_['at_risk'] else 0,
            'survival_at_max_time': self.survival_function_[-1],
        }


def plot_survival_data(
    *fitters: KaplanMeierFitter,
) -> Dict[str, List[Dict]]:
    """
    Get data for comparing multiple survival curves.

    Parameters
    ----------
    *fitters : KaplanMeierFitter
        One or more fitted KM estimators.

    Returns
    -------
    data : dict
        Data for plotting.
    """
    curves = []
    for fitter in fitters:
        curves.append(fitter.plot_data())

    return {'curves': curves}


def median_survival_time(
    durations: np.ndarray,
    event_observed: Optional[np.ndarray] = None,
) -> float:
    """
    Compute median survival time.

    Parameters
    ----------
    durations : ndarray
        Observed durations.
    event_observed : ndarray, optional
        Event indicators.

    Returns
    -------
    median : float
        Median survival time.
    """
    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed)
    return kmf.median_survival_time_
