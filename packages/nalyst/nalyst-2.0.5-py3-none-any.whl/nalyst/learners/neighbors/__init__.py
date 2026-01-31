"""
Nearest Neighbors learners for Nalyst.

This module provides K-Nearest Neighbors implementations
for classification, regression, and outlier detection.
"""

from nalyst.learners.neighbors.classification import (
    KNeighborsClassifier,
    RadiusNeighborsClassifier,
    NearestCentroid,
)
from nalyst.learners.neighbors.regression import (
    KNeighborsRegressor,
    RadiusNeighborsRegressor,
)
from nalyst.learners.neighbors.unsupervised import (
    NearestNeighbors,
)
from nalyst.learners.neighbors.outlier import (
    LocalOutlierFactor,
)

__all__ = [
    # Classification
    "KNeighborsClassifier",
    "RadiusNeighborsClassifier",
    "NearestCentroid",
    # Regression
    "KNeighborsRegressor",
    "RadiusNeighborsRegressor",
    # Unsupervised
    "NearestNeighbors",
    # Outlier detection
    "LocalOutlierFactor",
]
