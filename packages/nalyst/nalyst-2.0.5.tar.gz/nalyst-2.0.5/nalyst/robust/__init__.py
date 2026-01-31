"""
Robust Regression for Nalyst.

Provides regression methods resistant to outliers.
"""

from nalyst.robust.rlm import (
    RobustLinearModel,
    HuberRegressor,
    TheilSenRegressor,
    RANSACRegressor,
)
from nalyst.robust.m_estimators import (
    Huber,
    Tukey,
    AndrewWave,
    Hampel,
    TrimmedMean,
)

__all__ = [
    # Models
    "RobustLinearModel",
    "HuberRegressor",
    "TheilSenRegressor",
    "RANSACRegressor",
    # M-estimators (weight functions)
    "Huber",
    "Tukey",
    "AndrewWave",
    "Hampel",
    "TrimmedMean",
]
