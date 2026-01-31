"""
Nonparametric Methods for Nalyst.

Provides kernel density estimation, kernel regression, and LOWESS.
"""

from nalyst.nonparametric.kde import (
    KernelDensity,
    gaussian_kde,
    silverman_bandwidth,
    scott_bandwidth,
)
from nalyst.nonparametric.kernel_regression import (
    KernelRegression,
    NadarayaWatson,
    LocalPolynomial,
)
from nalyst.nonparametric.lowess import (
    lowess,
    loess,
)

__all__ = [
    # Kernel Density
    "KernelDensity",
    "gaussian_kde",
    "silverman_bandwidth",
    "scott_bandwidth",
    # Kernel Regression
    "KernelRegression",
    "NadarayaWatson",
    "LocalPolynomial",
    # LOWESS/LOESS
    "lowess",
    "loess",
]
