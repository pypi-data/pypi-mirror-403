"""
Generalized Additive Models (GAM) for Nalyst.

Provides flexible nonparametric regression using smooth functions.
"""

from nalyst.gam.core import (
    GAM,
    LinearGAM,
    LogisticGAM,
    PoissonGAM,
    GammaGAM,
)
from nalyst.gam.terms import (
    s,
    l,
    f,
    te,
    SplineTerm,
    LinearTerm,
    FactorTerm,
    TensorTerm,
)

__all__ = [
    # Models
    "GAM",
    "LinearGAM",
    "LogisticGAM",
    "PoissonGAM",
    "GammaGAM",
    # Terms
    "s",
    "l",
    "f",
    "te",
    "SplineTerm",
    "LinearTerm",
    "FactorTerm",
    "TensorTerm",
]
