"""
Distribution families for GLM.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Type
import numpy as np

from nalyst.glm.links import Link, Identity, Log, Logit, InversePower, InverseSquared


class Family(ABC):
    """
    Abstract base class for GLM families.

    A family specifies the distribution of the response variable
    and the default link function.
    """

    link: Link
    variance_power: float = 0  # For Tweedie family

    @abstractmethod
    def variance(self, mu: np.ndarray) -> np.ndarray:
        """Variance function V(mu)."""
        pass

    @abstractmethod
    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        """Deviance for the family."""
        pass

    def deviance_residuals(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        """Deviance residuals."""
        d = self._unit_deviance(y, mu)
        return np.sign(y - mu) * np.sqrt(np.maximum(d, 0))

    @abstractmethod
    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        """Unit deviance for each observation."""
        pass

    def weights(self, mu: np.ndarray) -> np.ndarray:
        """Working weights for IRLS."""
        return 1 / (self.variance(mu) * self.link.deriv(mu) ** 2)

    def log_likelihood(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        """Log-likelihood (up to a constant)."""
        return -0.5 * self.deviance(y, mu, scale)


class Gaussian(Family):
    """
    Gaussian (Normal) family.

    For continuous response with constant variance.
    Default link: Identity
    """

    def __init__(self, link: Optional[Link] = None):
        self.link = link if link is not None else Identity()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return np.ones_like(mu)

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return np.sum((y - mu) ** 2) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        return (y - mu) ** 2


class Binomial(Family):
    """
    Binomial family.

    For binary or proportion response.
    Default link: Logit
    """

    def __init__(self, link: Optional[Link] = None):
        self.link = link if link is not None else Logit()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        return mu * (1 - mu)

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        mu = np.clip(mu, 1e-10, 1 - 1e-10)
        y = np.clip(y, 1e-10, 1 - 1e-10)

        d = 2 * (y * np.log(y / mu) + (1 - y) * np.log((1 - y) / (1 - mu)))
        return np.where(np.isfinite(d), d, 0)


class Poisson(Family):
    """
    Poisson family.

    For count data.
    Default link: Log
    """

    def __init__(self, link: Optional[Link] = None):
        self.link = link if link is not None else Log()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return np.maximum(mu, 1e-10)

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return 2 * np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        y_safe = np.maximum(y, 1e-10)

        d = y * np.log(y_safe / mu) - (y - mu)
        return np.where(y > 0, d, mu)


class Gamma(Family):
    """
    Gamma family.

    For positive continuous data with variance proportional to mean squared.
    Default link: Inverse (1/mu)
    """

    def __init__(self, link: Optional[Link] = None):
        self.link = link if link is not None else InversePower(power=1)

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return np.maximum(mu, 1e-10) ** 2

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return 2 * np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        y = np.maximum(y, 1e-10)

        return (y - mu) / mu - np.log(y / mu)


class NegativeBinomial(Family):
    """
    Negative Binomial family.

    For overdispersed count data.
    Default link: Log

    Parameters
    ----------
    alpha : float, default=1.0
        Dispersion parameter (alpha = 1/theta where theta is the shape).
    """

    def __init__(self, alpha: float = 1.0, link: Optional[Link] = None):
        self.alpha = alpha
        self.link = link if link is not None else Log()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return mu + self.alpha * mu ** 2

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return 2 * np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        y = np.maximum(y, 0)

        theta = 1 / self.alpha

        d = np.zeros_like(y, dtype=float)

        mask = y > 0
        d[mask] = y[mask] * np.log(y[mask] / mu[mask])
        d += (y + theta) * np.log((mu + theta) / (y + theta))

        return 2 * d


class Tweedie(Family):
    """
    Tweedie family.

    For data with power variance function V(mu) = mu^p.

    Parameters
    ----------
    variance_power : float
        Power parameter p:
        - p=0: Gaussian
        - p=1: Poisson
        - p=2: Gamma
        - p=3: Inverse Gaussian
        - 1<p<2: Compound Poisson-Gamma (good for zero-inflated continuous)
    link : Link, optional
        Link function. Default is Log.
    """

    def __init__(self, variance_power: float = 1.5, link: Optional[Link] = None):
        self.variance_power = variance_power
        self.link = link if link is not None else Log()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return np.power(np.maximum(mu, 1e-10), self.variance_power)

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        p = self.variance_power
        mu = np.maximum(mu, 1e-10)
        y = np.maximum(y, 0)

        if p == 0:
            return (y - mu) ** 2
        elif p == 1:
            return 2 * (y * np.log(np.maximum(y, 1e-10) / mu) - (y - mu))
        elif p == 2:
            return 2 * ((y - mu) / mu - np.log(np.maximum(y, 1e-10) / mu))
        else:
            # General case
            d = y ** (2 - p) / ((1 - p) * (2 - p))
            d -= y * mu ** (1 - p) / (1 - p)
            d += mu ** (2 - p) / (2 - p)
            return 2 * d


class InverseGaussian(Family):
    """
    Inverse Gaussian family.

    For positive continuous data with variance proportional to mu^3.
    Default link: Inverse Squared (1/mu^2)
    """

    def __init__(self, link: Optional[Link] = None):
        self.link = link if link is not None else InverseSquared()

    def variance(self, mu: np.ndarray) -> np.ndarray:
        return np.maximum(mu, 1e-10) ** 3

    def deviance(self, y: np.ndarray, mu: np.ndarray, scale: float = 1.0) -> float:
        return np.sum(self._unit_deviance(y, mu)) / scale

    def _unit_deviance(self, y: np.ndarray, mu: np.ndarray) -> np.ndarray:
        mu = np.maximum(mu, 1e-10)
        y = np.maximum(y, 1e-10)

        return (y - mu) ** 2 / (y * mu ** 2)
