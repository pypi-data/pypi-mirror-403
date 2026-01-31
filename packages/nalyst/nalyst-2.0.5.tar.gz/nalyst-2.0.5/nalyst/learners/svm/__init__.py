"""
Support Vector Machine learners for Nalyst.

This module provides SVM implementations for
classification, regression, and outlier detection.
"""

from nalyst.learners.svm.classification import (
    SupportVectorClassifier,
    LinearSVC,
    NuSVC,
)
from nalyst.learners.svm.regression import (
    SupportVectorRegressor,
    LinearSVR,
    NuSVR,
)
from nalyst.learners.svm.outlier import (
    OneClassSVM,
)

__all__ = [
    # Classification
    "SupportVectorClassifier",
    "LinearSVC",
    "NuSVC",
    # Regression
    "SupportVectorRegressor",
    "LinearSVR",
    "NuSVR",
    # Outlier detection
    "OneClassSVM",
]
