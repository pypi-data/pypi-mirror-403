"""
Parametric survival models.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import numpy as np
from scipy.optimize import minimize
from scipy.special import gamma as gamma_fn


class ParametricSurvivalFitter:
    """Base class for parametric survival models."""

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> float:
        """Compute negative log-likelihood."""
        raise NotImplementedError

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
    ) -> "ParametricSurvivalFitter":
        """Fit the model."""
        raise NotImplementedError

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute survival function at given times."""
        raise NotImplementedError

    def hazard_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute hazard function at given times."""
        raise NotImplementedError


class WeibullFitter(ParametricSurvivalFitter):
    """
    Weibull parametric survival model.

    S(t) = exp(-(t/lambda)^rho)

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level for confidence intervals.

    Attributes
    ----------
    lambda_ : float
        Scale parameter.
    rho_ : float
        Shape parameter.
    median_survival_time_ : float
        Median survival time.

    Examples
    --------
    >>> from nalyst.survival import WeibullFitter
    >>> wf = WeibullFitter()
    >>> wf.fit(durations, event_observed)
    >>> print(wf.lambda_, wf.rho_)
    """

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> float:
        """Weibull negative log-likelihood."""
        log_lambda, log_rho = params
        lam = np.exp(log_lambda)
        rho = np.exp(log_rho)

        # Log-likelihood
        # L = sum(events * (log(rho) + (rho-1)*log(t) - rho*log(lambda)) - (t/lambda)^rho)
        t = durations + 1e-10  # Avoid log(0)

        ll = np.sum(
            events * (np.log(rho) + (rho - 1) * np.log(t) - rho * np.log(lam)) -
            (t / lam) ** rho
        )

        return -ll

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
    ) -> "WeibullFitter":
        """
        Fit Weibull model.

        Parameters
        ----------
        durations : ndarray
            Observed durations.
        event_observed : ndarray, optional
            Event indicators.

        Returns
        -------
        self
        """
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        # Initial estimates
        log_lambda_init = np.log(np.median(durations) + 1)
        log_rho_init = 0.0  # rho = 1

        # Optimize
        result = minimize(
            self._negative_log_likelihood,
            x0=[log_lambda_init, log_rho_init],
            args=(durations, event_observed),
            method='Nelder-Mead',
        )

        self.lambda_ = np.exp(result.x[0])
        self.rho_ = np.exp(result.x[1])

        # Median survival time: S(t) = 0.5 => t = lambda * log(2)^(1/rho)
        self.median_survival_time_ = self.lambda_ * (np.log(2) ** (1 / self.rho_))

        self._nll = result.fun
        self._durations = durations
        self._events = event_observed

        return self

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute Weibull survival function."""
        times = np.asarray(times)
        return np.exp(-((times / self.lambda_) ** self.rho_))

    def hazard_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute Weibull hazard function."""
        times = np.asarray(times) + 1e-10
        return (self.rho_ / self.lambda_) * ((times / self.lambda_) ** (self.rho_ - 1))

    def mean_survival_time(self) -> float:
        """Compute mean survival time."""
        return self.lambda_ * gamma_fn(1 + 1 / self.rho_)


class ExponentialFitter(ParametricSurvivalFitter):
    """
    Exponential parametric survival model.

    S(t) = exp(-t/lambda) = exp(-lambda * t)

    Special case of Weibull with rho = 1.

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level.

    Attributes
    ----------
    lambda_ : float
        Rate parameter (hazard).
    median_survival_time_ : float
        Median survival time.

    Examples
    --------
    >>> from nalyst.survival import ExponentialFitter
    >>> ef = ExponentialFitter()
    >>> ef.fit(durations, event_observed)
    """

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> float:
        """Exponential negative log-likelihood."""
        log_lambda = params[0]
        lam = np.exp(log_lambda)

        # LL = sum(events * log(lambda) - lambda * t)
        ll = np.sum(events * log_lambda - lam * durations)

        return -ll

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
    ) -> "ExponentialFitter":
        """Fit exponential model."""
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        # MLE: lambda = n_events / sum(durations)
        n_events = np.sum(event_observed)
        total_time = np.sum(durations)

        self.lambda_ = n_events / total_time if total_time > 0 else 1

        self.median_survival_time_ = np.log(2) / self.lambda_

        return self

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute exponential survival function."""
        times = np.asarray(times)
        return np.exp(-self.lambda_ * times)

    def hazard_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute exponential hazard (constant)."""
        times = np.asarray(times)
        return np.full_like(times, self.lambda_, dtype=float)


class LogNormalFitter(ParametricSurvivalFitter):
    """
    Log-normal parametric survival model.

    log(T) ~ Normal(mu, sigma^2)

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level.

    Attributes
    ----------
    mu_ : float
        Mean of log(T).
    sigma_ : float
        Std of log(T).
    median_survival_time_ : float
        Median survival time.

    Examples
    --------
    >>> from nalyst.survival import LogNormalFitter
    >>> lnf = LogNormalFitter()
    >>> lnf.fit(durations, event_observed)
    """

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> float:
        """Log-normal negative log-likelihood."""
        from scipy.stats import norm

        mu, log_sigma = params
        sigma = np.exp(log_sigma)

        log_t = np.log(durations + 1e-10)
        z = (log_t - mu) / sigma

        # For events: f(t) = (1/t) * phi((log(t) - mu)/sigma) / sigma
        # For censored: S(t) = 1 - Phi((log(t) - mu)/sigma)

        ll_events = events * (
            -np.log(durations + 1e-10) - np.log(sigma) + norm.logpdf(z)
        )

        ll_censored = (1 - events) * norm.logsf(z)

        return -np.sum(ll_events + ll_censored)

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
    ) -> "LogNormalFitter":
        """Fit log-normal model."""
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        # Initial estimates from log(durations)
        log_t = np.log(durations + 1e-10)
        mu_init = np.mean(log_t[event_observed == 1]) if np.any(event_observed) else np.mean(log_t)
        sigma_init = np.std(log_t[event_observed == 1]) if np.any(event_observed) else np.std(log_t)

        result = minimize(
            self._negative_log_likelihood,
            x0=[mu_init, np.log(sigma_init + 0.1)],
            args=(durations, event_observed),
            method='Nelder-Mead',
        )

        self.mu_ = result.x[0]
        self.sigma_ = np.exp(result.x[1])

        self.median_survival_time_ = np.exp(self.mu_)

        return self

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute log-normal survival function."""
        from scipy.stats import norm

        times = np.asarray(times)
        log_t = np.log(times + 1e-10)
        z = (log_t - self.mu_) / self.sigma_

        return 1 - norm.cdf(z)

    def hazard_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute log-normal hazard function."""
        from scipy.stats import norm

        times = np.asarray(times) + 1e-10
        log_t = np.log(times)
        z = (log_t - self.mu_) / self.sigma_

        f = norm.pdf(z) / (self.sigma_ * times)
        S = 1 - norm.cdf(z)

        return f / (S + 1e-10)


class LogLogisticFitter(ParametricSurvivalFitter):
    """
    Log-logistic parametric survival model.

    S(t) = 1 / (1 + (t/alpha)^beta)

    Parameters
    ----------
    alpha : float, default=0.05
        Significance level.

    Attributes
    ----------
    alpha_param_ : float
        Scale parameter.
    beta_ : float
        Shape parameter.
    median_survival_time_ : float
        Median survival time.

    Examples
    --------
    >>> from nalyst.survival import LogLogisticFitter
    >>> llf = LogLogisticFitter()
    >>> llf.fit(durations, event_observed)
    """

    def _negative_log_likelihood(
        self,
        params: np.ndarray,
        durations: np.ndarray,
        events: np.ndarray,
    ) -> float:
        """Log-logistic negative log-likelihood."""
        log_alpha, log_beta = params
        alpha = np.exp(log_alpha)
        beta = np.exp(log_beta)

        t = durations + 1e-10

        # f(t) = (beta/alpha) * (t/alpha)^(beta-1) / (1 + (t/alpha)^beta)^2
        # S(t) = 1 / (1 + (t/alpha)^beta)

        ta = t / alpha
        ta_beta = ta ** beta

        log_f = np.log(beta) - np.log(alpha) + (beta - 1) * np.log(ta) - 2 * np.log(1 + ta_beta)
        log_S = -np.log(1 + ta_beta)

        ll = np.sum(events * log_f + (1 - events) * log_S)

        return -ll

    def fit(
        self,
        durations: np.ndarray,
        event_observed: Optional[np.ndarray] = None,
    ) -> "LogLogisticFitter":
        """Fit log-logistic model."""
        durations = np.asarray(durations).flatten()

        if event_observed is None:
            event_observed = np.ones(len(durations), dtype=int)
        else:
            event_observed = np.asarray(event_observed).flatten().astype(int)

        # Initial estimates
        log_alpha_init = np.log(np.median(durations) + 1)
        log_beta_init = 0.0

        result = minimize(
            self._negative_log_likelihood,
            x0=[log_alpha_init, log_beta_init],
            args=(durations, event_observed),
            method='Nelder-Mead',
        )

        self.alpha_param_ = np.exp(result.x[0])
        self.beta_ = np.exp(result.x[1])

        # Median: S(t) = 0.5 => (t/alpha)^beta = 1 => t = alpha
        self.median_survival_time_ = self.alpha_param_

        return self

    def survival_function_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute log-logistic survival function."""
        times = np.asarray(times)
        ta_beta = (times / self.alpha_param_) ** self.beta_
        return 1 / (1 + ta_beta)

    def hazard_at_times(self, times: np.ndarray) -> np.ndarray:
        """Compute log-logistic hazard function."""
        times = np.asarray(times) + 1e-10
        ta = times / self.alpha_param_
        ta_beta = ta ** self.beta_

        return (self.beta_ / self.alpha_param_) * (ta ** (self.beta_ - 1)) / (1 + ta_beta)
