"""
Link functions for GLM.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
from scipy import stats


class Link(ABC):
    """
    Abstract base class for link functions.

    A link function g(mu) relates the linear predictor to the mean:
    eta = g(mu)
    """

    @abstractmethod
    def __call__(self, mu: np.ndarray) -> np.ndarray:
        """Apply link function: eta = g(mu)."""
        pass

    @abstractmethod
    def inverse(self, eta: np.ndarray) -> np.ndarray:
        """Inverse link: mu = g^(-1)(eta)."""
        pass

    @abstractmethod
    def deriv(self, mu: np.ndarray) -> np.ndarray:
        """Derivative of link: g'(mu)."""
        pass

    def inverse_deriv(self, eta: np.ndarray) -> np.ndarray:
        """Derivative of inverse link."""
        mu = self.inverse(eta)
        return 1 / self.deriv(mu)


class Identity(Link):
    """
    Identity link: g(mu) = mu

    Used for Gaussian (normal) family.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        return mu

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        return eta

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        return np.ones_like(mu)


class Log(Link):
    """
    Log link: g(mu) = log(mu)

    Used for Poisson, Gamma, and other positive-valued distributions.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        return np.log(np.maximum(mu, 1e-10))

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        return np.exp(np.clip(eta, -700, 700))

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        return 1 / np.maximum(mu, 1e-10)


class Logit(Link):
    """
    Logit link: g(mu) = log(mu / (1 - mu))

    Used for Binomial family.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return np.log(mu / (1 - mu))

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        eta = np.clip(eta, -700, 700)
        return 1 / (1 + np.exp(-eta))

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return 1 / (mu * (1 - mu))


class Probit(Link):
    """
    Probit link: g(mu) = Phi^(-1)(mu)

    Where Phi is the standard normal CDF.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return stats.norm.ppf(mu)

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        return stats.norm.cdf(eta)

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return 1 / stats.norm.pdf(stats.norm.ppf(mu))


class CLogLog(Link):
    """
    Complementary log-log link: g(mu) = log(-log(1 - mu))

    Asymmetric alternative to logit for binary outcomes.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return np.log(-np.log(1 - mu))

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        eta = np.clip(eta, -700, 700)
        return 1 - np.exp(-np.exp(eta))

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return 1 / ((1 - mu) * (-np.log(1 - mu)))


class Power(Link):
    """
    Power link: g(mu) = mu^power

    Parameters
    ----------
    power : float
        Power parameter. Special cases:
        - power=1: Identity
        - power=0: Log
        - power=-1: Inverse
    """

    def __init__(self, power: float = 1.0):
        self.power = power

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        if self.power == 0:
            return np.log(np.maximum(mu, 1e-10))
        else:
            return np.power(np.maximum(mu, 1e-10), self.power)

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        if self.power == 0:
            return np.exp(np.clip(eta, -700, 700))
        else:
            return np.power(np.maximum(eta, 1e-10), 1 / self.power)

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        if self.power == 0:
            return 1 / np.maximum(mu, 1e-10)
        else:
            return self.power * np.power(np.maximum(mu, 1e-10), self.power - 1)


class InversePower(Link):
    """
    Inverse power link: g(mu) = 1 / mu^power

    Parameters
    ----------
    power : float, default=1.0
        Power parameter.
    """

    def __init__(self, power: float = 1.0):
        self.power = power

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        return 1 / np.power(np.maximum(mu, 1e-10), self.power)

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        return np.power(1 / np.maximum(eta, 1e-10), 1 / self.power)

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        return -self.power / np.power(np.maximum(mu, 1e-10), self.power + 1)


class InverseSquared(Link):
    """
    Inverse squared link: g(mu) = 1 / mu^2

    Used for Inverse Gaussian family.
    """

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        return 1 / np.maximum(mu, 1e-10) ** 2

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        return 1 / np.sqrt(np.maximum(eta, 1e-10))

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        return -2 / np.maximum(mu, 1e-10) ** 3


class NegativeBinomialLink(Link):
    """
    Negative binomial link: g(mu) = log(mu / (mu + alpha))

    Parameters
    ----------
    alpha : float
        Dispersion parameter.
    """

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha

    def __call__(self, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        return np.log(mu / (mu + self.alpha))

    def inverse(self, eta: np.ndarray) -> np.ndarray:
        eta = np.clip(eta, -700, 700)
        expeta = np.exp(eta)
        return self.alpha * expeta / (1 - expeta)

    def deriv(self, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        return self.alpha / (mu * (mu + self.alpha))
