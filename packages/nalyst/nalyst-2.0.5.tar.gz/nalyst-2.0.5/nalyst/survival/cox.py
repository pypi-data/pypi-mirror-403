"""
Cox Proportional Hazards model.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
import numpy as np


class CoxPHFitter:
    """
    Cox Proportional Hazards regression.

    Semi-parametric survival model for estimating hazard ratios
    of covariates.

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level for confidence intervals.
    penalizer : float, default=0.0
        L2 regularization penalty.
    max_iter : int, default=100
        Maximum Newton-Raphson iterations.
    tol : float, default=1e-6
        Convergence tolerance.

    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Log-hazard ratios.
    hazard_ratios_ : ndarray
        Exponentiated coefficients.
    se_ : ndarray
        Standard errors.
    confidence_intervals_ : dict
        CI bounds for each coefficient.
    baseline_hazard_ : ndarray
        Baseline hazard function.

    Examples
    --------
    >>> from nalyst.survival import CoxPHFitter
    >>> cph = CoxPHFitter()
    >>> cph.fit(X, durations, event_observed)
    >>> print(cph.hazard_ratios_)
    """

    def __init__(
        self,
        alpha: float = 0.05,
        penalizer: float = 0.0,
        max_iter: int = 100,
        tol: float = 1e-6,
    ):
        self.alpha = alpha
        self.penalizer = penalizer
        self.max_iter = max_iter
        self.tol = tol

    def fit(
        self,
        X: np.ndarray,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
    ) -> "CoxPHFitter":
        """
        Fit Cox proportional hazards model.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Covariate matrix.
        durations : ndarray of shape (n_samples,)
            Observed durations.
        event_observed : ndarray of shape (n_samples,), optional
            Event indicators (1=event, 0=censored).
        feature_names : list of str, optional
            Names of features.

        Returns
        -------
        self
        """
        X = np.asarray(X)
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        n_samples, n_features = X.shape

        if feature_names is None:
            self.feature_names_ = [f"x{i}" for i in range(n_features)]
        else:
            self.feature_names_ = feature_names

        # Sort by time
        order = np.argsort(durations)
        X = X[order]
        durations = durations[order]
        event_observed = event_observed[order]

        # Initialize coefficients
        beta = np.zeros(n_features)

        # Newton-Raphson optimization
        for iteration in range(self.max_iter):
            # Compute risk set quantities
            gradient, hessian = self._compute_gradient_hessian(
                beta, X, durations, event_observed
            )

            # Add L2 penalty
            gradient -= self.penalizer * beta
            hessian -= self.penalizer * np.eye(n_features)

            # Newton step
            try:
                step = np.linalg.solve(-hessian, gradient)
            except np.linalg.LinAlgError:
                step = -0.1 * gradient

            beta_new = beta + step

            # Check convergence
            if np.max(np.abs(step)) < self.tol:
                beta = beta_new
                break

            beta = beta_new

        self.coef_ = beta
        self.hazard_ratios_ = np.exp(beta)

        # Compute standard errors
        _, hessian = self._compute_gradient_hessian(
            beta, X, durations, event_observed
        )

        try:
            cov = np.linalg.inv(-hessian)
            self.se_ = np.sqrt(np.diag(cov))
        except np.linalg.LinAlgError:
            self.se_ = np.ones(n_features) * np.nan

        # Confidence intervals
        from scipy.stats import norm
        z = norm.ppf(1 - self.alpha / 2)

        self.confidence_intervals_ = {}
        for i, name in enumerate(self.feature_names_):
            hr_lower = np.exp(beta[i] - z * self.se_[i])
            hr_upper = np.exp(beta[i] + z * self.se_[i])
            self.confidence_intervals_[name] = (hr_lower, hr_upper)

        # Baseline hazard
        self._compute_baseline_hazard(X, durations, event_observed)

        # Store sorted data
        self._X = X
        self._durations = durations
        self._event_observed = event_observed

        return self

    def _compute_gradient_hessian(
        self,
        beta: np.ndarray,
        X: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> tuple:
        """Compute gradient and Hessian of partial likelihood."""
        n_samples, n_features = X.shape

        # Exp(X @ beta)
        risk = np.exp(X @ beta)

        gradient = np.zeros(n_features)
        hessian = np.zeros((n_features, n_features))

        # Process each event time
        unique_times = np.unique(durations[events == 1])

        for t in unique_times:
            # At-risk set: all with duration >= t
            at_risk = durations >= t

            # Events at time t
            event_at_t = (durations == t) & (events == 1)

            if not np.any(at_risk):
                continue

            # Risk-set sums
            risk_sum = np.sum(risk[at_risk])
            X_risk = X[at_risk]
            risk_at_risk = risk[at_risk]

            # Weighted mean of X
            weighted_X = np.sum(X_risk * risk_at_risk[:, np.newaxis], axis=0) / risk_sum

            # Update gradient
            for i in np.where(event_at_t)[0]:
                gradient += X[i] - weighted_X

            # Weighted second moment
            n_events = np.sum(event_at_t)
            for i in np.where(event_at_t)[0]:
                weighted_X2 = np.sum(
                    (X_risk * risk_at_risk[:, np.newaxis]).T @ X_risk,
                    axis=0
                ).reshape(n_features, n_features) / risk_sum

                hessian -= weighted_X2 - np.outer(weighted_X, weighted_X)

        return gradient, hessian

    def _compute_baseline_hazard(
        self,
        X: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ):
        """Compute Breslow baseline hazard estimator."""
        risk_scores = np.exp(X @ self.coef_)

        unique_times = np.unique(durations[events == 1])

        timeline = []
        baseline_hazard = []
        cumulative_hazard = 0

        for t in unique_times:
            at_risk = durations >= t
            events_at_t = (durations == t) & (events == 1)

            d = np.sum(events_at_t)
            risk_sum = np.sum(risk_scores[at_risk])

            h0 = d / risk_sum if risk_sum > 0 else 0

            timeline.append(t)
            baseline_hazard.append(h0)
            cumulative_hazard += h0

        self.baseline_timeline_ = np.array(timeline)
        self.baseline_hazard_ = np.array(baseline_hazard)
        self.baseline_cumulative_hazard_ = np.cumsum(baseline_hazard)

    def predict_partial_hazard(self, X: np.ndarray) -> np.ndarray:
        """
        Predict partial hazard (exp(X @ beta)).

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Covariates.

        Returns
        -------
        hazard : ndarray
            Partial hazard values.
        """
        X = np.asarray(X)
        return np.exp(X @ self.coef_)

    def predict_survival_function(
        self,
        X: np.ndarray,
        times: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Predict survival function for new data.

        Parameters
        ----------
        X : ndarray of shape (n_samples, n_features)
            Covariates.
        times : ndarray, optional
            Times at which to evaluate. Default: all event times.

        Returns
        -------
        survival : ndarray of shape (n_samples, n_times)
            Survival probabilities.
        """
        X = np.asarray(X)

        if times is None:
            times = self.baseline_timeline_

        hazard = self.predict_partial_hazard(X)

        survival = np.zeros((len(X), len(times)))

        for j, t in enumerate(times):
            # Find cumulative baseline hazard at time t
            idx = np.searchsorted(self.baseline_timeline_, t, side='right')
            if idx > 0:
                H0 = self.baseline_cumulative_hazard_[idx - 1]
            else:
                H0 = 0

            # S(t|X) = exp(-H0(t) * exp(X @ beta))
            survival[:, j] = np.exp(-H0 * hazard)

        return survival

    def summary(self) -> Dict[str, Any]:
        """
        Get model summary.

        Returns
        -------
        summary : dict
            Coefficients, hazard ratios, confidence intervals, p-values.
        """
        from scipy.stats import norm

        z_scores = self.coef_ / self.se_
        p_values = 2 * (1 - norm.cdf(np.abs(z_scores)))

        summary = []
        for i, name in enumerate(self.feature_names_):
            summary.append({
                'feature': name,
                'coef': self.coef_[i],
                'hazard_ratio': self.hazard_ratios_[i],
                'se': self.se_[i],
                'z': z_scores[i],
                'p': p_values[i],
                'ci_lower': self.confidence_intervals_[name][0],
                'ci_upper': self.confidence_intervals_[name][1],
            })

        return {'coefficients': summary}


def check_proportional_hazards(
    cph: CoxPHFitter,
    X: Optional[np.ndarray] = None,
    durations: Optional[np.ndarray] = None,
    event_observed: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Test the proportional hazards assumption.

    Uses Schoenfeld residuals to test PH assumption.

    Parameters
    ----------
    cph : CoxPHFitter
        Fitted Cox model.
    X, durations, event_observed : ndarray, optional
        Data (uses fitted data if not provided).

    Returns
    -------
    results : dict
        Test statistics and p-values for each covariate.
    """
    if X is None:
        X = cph._X
        durations = cph._durations
        event_observed = cph._event_observed

    X = np.asarray(X)
    n_samples, n_features = X.shape

    # Compute Schoenfeld residuals
    residuals = []
    times = []

    unique_event_times = np.unique(durations[event_observed == 1])

    for t in unique_event_times:
        at_risk = durations >= t
        event_at_t = (durations == t) & (event_observed == 1)

        if not np.any(at_risk) or not np.any(event_at_t):
            continue

        risk_scores = np.exp(X[at_risk] @ cph.coef_)
        risk_sum = np.sum(risk_scores)

        # Expected X at time t
        expected_X = np.sum(X[at_risk] * risk_scores[:, np.newaxis], axis=0) / risk_sum

        # Residual for each event
        for i in np.where(event_at_t)[0]:
            residuals.append(X[i] - expected_X)
            times.append(t)

    residuals = np.array(residuals)
    times = np.array(times)

    # Test correlation of residuals with time
    from scipy.stats import spearmanr

    results = {}
    for j, name in enumerate(cph.feature_names_):
        if len(residuals) > 0:
            corr, pvalue = spearmanr(times, residuals[:, j])
        else:
            corr, pvalue = 0, 1

        results[name] = {
            'correlation': corr,
            'p_value': pvalue,
            'ph_violated': pvalue < 0.05,
        }

    return results
