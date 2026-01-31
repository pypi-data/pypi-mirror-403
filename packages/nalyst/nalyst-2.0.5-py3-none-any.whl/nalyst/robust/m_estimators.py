"""
M-estimator weight functions for robust regression.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class MEstimator(ABC):
    """Base class for M-estimators."""

    def __init__(self, c: float):
        """
        Parameters
        ----------
        c : float
            Tuning constant.
        """
        self.c = c

    @abstractmethod
    def rho(self, u: np.ndarray) -> np.ndarray:
        """
        The M-estimator rho function.

        Parameters
        ----------
        u : ndarray
            Standardized residuals.

        Returns
        -------
        rho : ndarray
            Loss values.
        """
        pass

    @abstractmethod
    def psi(self, u: np.ndarray) -> np.ndarray:
        """
        The M-estimator psi (derivative of rho).

        Parameters
        ----------
        u : ndarray
            Standardized residuals.

        Returns
        -------
        psi : ndarray
            Influence function values.
        """
        pass

    def weights(self, u: np.ndarray) -> np.ndarray:
        """
        IRLS weights: psi(u) / u.

        Parameters
        ----------
        u : ndarray
            Standardized residuals.

        Returns
        -------
        weights : ndarray
            IRLS weights.
        """
        with np.errstate(divide='ignore', invalid='ignore'):
            w = np.where(u != 0, self.psi(u) / u, 1.0)
        return np.clip(w, 0, 1e10)


class Huber(MEstimator):
    """
    Huber's M-estimator.

    Uses L2 loss for small residuals and L1 for large residuals.

    Parameters
    ----------
    c : float, default=1.345
        Tuning constant. Default gives 95% efficiency for Gaussian.

    Examples
    --------
    >>> from nalyst.robust import Huber
    >>> huber = Huber(c=1.345)
    >>> weights = huber.weights(residuals / scale)
    """

    def __init__(self, c: float = 1.345):
        super().__init__(c)

    def rho(self, u: np.ndarray) -> np.ndarray:
        """Huber rho function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(
            abs_u <= self.c,
            0.5 * u ** 2,
            self.c * abs_u - 0.5 * self.c ** 2
        )

    def psi(self, u: np.ndarray) -> np.ndarray:
        """Huber psi function (derivative of rho)."""
        u = np.asarray(u)
        return np.clip(u, -self.c, self.c)

    def weights(self, u: np.ndarray) -> np.ndarray:
        """Huber weights."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(abs_u <= self.c, 1.0, self.c / abs_u)


class Tukey(MEstimator):
    """
    Tukey's biweight (bisquare) M-estimator.

    Completely rejects outliers beyond c.

    Parameters
    ----------
    c : float, default=4.685
        Tuning constant. Default gives 95% efficiency for Gaussian.

    Examples
    --------
    >>> from nalyst.robust import Tukey
    >>> tukey = Tukey(c=4.685)
    >>> weights = tukey.weights(residuals / scale)
    """

    def __init__(self, c: float = 4.685):
        super().__init__(c)

    def rho(self, u: np.ndarray) -> np.ndarray:
        """Tukey rho function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(
            abs_u <= self.c,
            (self.c ** 2 / 6) * (1 - (1 - (u / self.c) ** 2) ** 3),
            self.c ** 2 / 6
        )

    def psi(self, u: np.ndarray) -> np.ndarray:
        """Tukey psi function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(
            abs_u <= self.c,
            u * (1 - (u / self.c) ** 2) ** 2,
            0.0
        )

    def weights(self, u: np.ndarray) -> np.ndarray:
        """Tukey weights."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(
            abs_u <= self.c,
            (1 - (u / self.c) ** 2) ** 2,
            0.0
        )


class AndrewWave(MEstimator):
    """
    Andrew's wave M-estimator.

    Uses sine wave for influence function.

    Parameters
    ----------
    c : float, default=1.339
        Tuning constant.

    Examples
    --------
    >>> from nalyst.robust import AndrewWave
    >>> andrew = AndrewWave()
    >>> weights = andrew.weights(residuals / scale)
    """

    def __init__(self, c: float = 1.339):
        super().__init__(c)

    def rho(self, u: np.ndarray) -> np.ndarray:
        """Andrew's wave rho function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        inside = abs_u <= np.pi * self.c

        rho = np.zeros_like(u, dtype=float)
        rho[inside] = self.c ** 2 * (1 - np.cos(u[inside] / self.c))
        rho[~inside] = 2 * self.c ** 2

        return rho

    def psi(self, u: np.ndarray) -> np.ndarray:
        """Andrew's wave psi function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        inside = abs_u <= np.pi * self.c

        psi = np.zeros_like(u, dtype=float)
        psi[inside] = self.c * np.sin(u[inside] / self.c)

        return psi

    def weights(self, u: np.ndarray) -> np.ndarray:
        """Andrew's wave weights."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        inside = abs_u <= np.pi * self.c

        weights = np.zeros_like(u, dtype=float)
        weights[inside] = np.sinc(u[inside] / (np.pi * self.c))

        return weights


class Hampel(MEstimator):
    """
    Hampel's three-part redescending M-estimator.

    Has three regions: linear, constant, and declining to zero.

    Parameters
    ----------
    a : float, default=2.0
        First breakpoint.
    b : float, default=4.0
        Second breakpoint.
    c : float, default=8.0
        Third breakpoint (rejection point).

    Examples
    --------
    >>> from nalyst.robust import Hampel
    >>> hampel = Hampel(a=2, b=4, c=8)
    >>> weights = hampel.weights(residuals / scale)
    """

    def __init__(
        self,
        a: float = 2.0,
        b: float = 4.0,
        c: float = 8.0,
    ):
        super().__init__(c)
        self.a = a
        self.b = b

    def rho(self, u: np.ndarray) -> np.ndarray:
        """Hampel rho function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        rho = np.zeros_like(u, dtype=float)

        # Region 1: |u| <= a
        mask1 = abs_u <= self.a
        rho[mask1] = 0.5 * u[mask1] ** 2

        # Region 2: a < |u| <= b
        mask2 = (abs_u > self.a) & (abs_u <= self.b)
        rho[mask2] = self.a * (abs_u[mask2] - 0.5 * self.a)

        # Region 3: b < |u| <= c
        mask3 = (abs_u > self.b) & (abs_u <= self.c)
        rho[mask3] = self.a * (
            self.b - 0.5 * self.a +
            (self.c - self.b) / 2 *
            (1 - ((self.c - abs_u[mask3]) / (self.c - self.b)) ** 2)
        )

        # Region 4: |u| > c
        mask4 = abs_u > self.c
        rho[mask4] = self.a * (self.b - 0.5 * self.a + (self.c - self.b) / 2)

        return rho

    def psi(self, u: np.ndarray) -> np.ndarray:
        """Hampel psi function."""
        u = np.asarray(u)
        abs_u = np.abs(u)
        sign_u = np.sign(u)

        psi = np.zeros_like(u, dtype=float)

        # Region 1: |u| <= a
        mask1 = abs_u <= self.a
        psi[mask1] = u[mask1]

        # Region 2: a < |u| <= b
        mask2 = (abs_u > self.a) & (abs_u <= self.b)
        psi[mask2] = self.a * sign_u[mask2]

        # Region 3: b < |u| <= c
        mask3 = (abs_u > self.b) & (abs_u <= self.c)
        psi[mask3] = self.a * sign_u[mask3] * (self.c - abs_u[mask3]) / (self.c - self.b)

        return psi

    def weights(self, u: np.ndarray) -> np.ndarray:
        """Hampel weights."""
        u = np.asarray(u)
        abs_u = np.abs(u) + 1e-10

        return self.psi(u) / u


class TrimmedMean(MEstimator):
    """
    Trimmed Mean M-estimator.

    Gives zero weight to observations beyond threshold.

    Parameters
    ----------
    c : float, default=2.0
        Trimming threshold in standard deviations.

    Examples
    --------
    >>> from nalyst.robust import TrimmedMean
    >>> tm = TrimmedMean(c=2.0)
    >>> weights = tm.weights(residuals / scale)
    """

    def __init__(self, c: float = 2.0):
        super().__init__(c)

    def rho(self, u: np.ndarray) -> np.ndarray:
        """Trimmed mean rho function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(abs_u <= self.c, 0.5 * u ** 2, 0.5 * self.c ** 2)

    def psi(self, u: np.ndarray) -> np.ndarray:
        """Trimmed mean psi function."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return np.where(abs_u <= self.c, u, 0.0)

    def weights(self, u: np.ndarray) -> np.ndarray:
        """Trimmed mean weights."""
        u = np.asarray(u)
        abs_u = np.abs(u)

        return (abs_u <= self.c).astype(float)
