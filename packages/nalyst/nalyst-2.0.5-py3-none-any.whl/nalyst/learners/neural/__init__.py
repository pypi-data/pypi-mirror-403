"""
Neural network learners for Nalyst.

This module provides multi-layer perceptron implementations
for classification and regression tasks.
"""

from nalyst.learners.neural.mlp import (
    MLPClassifier,
    MLPRegressor,
)

__all__ = [
    "MLPClassifier",
    "MLPRegressor",
]
